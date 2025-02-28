# Standard library imports
import os  # File system operations and environment variable access
import tempfile  # Create temporary files and directories for scanning
import shutil  # File operations including deletion of temporary files
import subprocess  # Execute external scanning tools as subprocesses
from typing import Dict, Optional  # Type hints for better code documentation
import enum  # Define scan result enumeration
from datetime import datetime  # Timestamp scan operations and track scanner health

# Third-party imports
import clamd  # Python interface to ClamAV daemon for virus scanning # version: ~=1.0.2

# Internal imports
from ..config import get_config  # Get environment-specific scanner configuration
from ....common.logging.logger import get_logger  # Get configured logger for the scanner service
from .storage_service import StorageService  # Access storage to retrieve files for scanning
from ....common.exceptions.api_exceptions import DependencyError  # Handle scanner dependency failure scenarios


# Initialize logger
logger = get_logger(__name__)

# Get configuration
config = get_config()

# Define temporary scan directory
TEMP_SCAN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_scan')


class ScanResult(enum.Enum):
    """
    Enumeration of possible file scan results
    """
    CLEAN = "clean"  # Define CLEAN value for files with no threats detected
    INFECTED = "infected"  # Define INFECTED value for files with viruses or malware detected
    ERROR = "error"  # Define ERROR value for when scanning process fails
    UNSUPPORTED = "unsupported"  # Define UNSUPPORTED value for file types that cannot be scanned


class ScannerService:
    """
    Service that provides virus/malware scanning capabilities for uploaded files
    """

    def __init__(self, storage_service: StorageService):
        """
        Initialize the scanner service with configuration
        """
        # Get scanner configuration from environment settings
        scanner_config = config.get_scanner_config()

        # Check if scanning is enabled in configuration
        self._enabled = scanner_config['enabled']

        # Determine scanner type (clamav, mock, custom)
        self._scanner_type = scanner_config['type']

        # Initialize the appropriate scanner based on type
        self._scanner_instance = None
        if self._enabled:
            if self._scanner_type == 'clamav':
                self._scanner_instance = self._init_clamav_scanner()
            elif self._scanner_type == 'mock':
                self._scanner_instance = self._init_mock_scanner()
            else:
                logger.warning(f"Unknown scanner type: {self._scanner_type}. Scanning will be disabled.")
                self._enabled = False

        # Store StorageService instance for file retrieval
        self._storage_service = storage_service

        # Ensure temporary scanning directory exists
        self._temp_directory = TEMP_SCAN_DIR
        self._create_temp_directory()

        # Set initial health status to unknown (None)
        self._last_health_check = None
        self._is_healthy = None

        # Log scanner service initialization
        logger.info(f"ScannerService initialized with type: {self._scanner_type}, enabled: {self._enabled}")

    def scan_file(self, storage_key: str) -> Dict:
        """
        Scan a file for viruses and malware
        """
        # Log scan request for the file
        logger.info(f"Scanning file: {storage_key}")

        # Check if scanning is enabled, return CLEAN if disabled
        if not self._enabled:
            logger.warning("File scanning is disabled. Returning CLEAN result.")
            return {"status": ScanResult.CLEAN.value, "details": "Scanning disabled"}

        # Create a temporary file for scanning
        temp_file_path = os.path.join(self._temp_directory, os.path.basename(storage_key))

        try:
            # Download file from quarantine storage
            self._storage_service.download_file(storage_key, temp_file_path)

            # Call the appropriate scanner method based on scanner type
            if self._scanner_type == 'clamav':
                scan_result = self._scan_with_clamav(temp_file_path)
            elif self._scanner_type == 'mock':
                scan_result = self._scan_with_mock(temp_file_path)
            else:
                scan_result = self._scan_with_custom(temp_file_path)

            # Log scan results and cleanup temporary files
            logger.info(f"Scan result for {storage_key}: {scan_result}")
            return scan_result

        except Exception as e:
            logger.error(f"Error scanning file {storage_key}: {str(e)}", exc_info=True)
            return {"status": ScanResult.ERROR.value, "details": str(e)}
        finally:
            # Cleanup temporary files
            self._cleanup_temp_files(temp_file_path)

    def _init_clamav_scanner(self) -> Optional[clamd.Clamd]:
        """
        Initialize ClamAV virus scanner
        """
        # Import clamd module
        try:
            # Get ClamAV configuration (host, port, socket)
            clamav_config = config.get_scanner_config()['clamav']
            clamav_host = clamav_config['host']
            clamav_port = clamav_config['port']
            clamav_socket = clamav_config['socket']

            # Try to connect to ClamAV daemon
            if clamav_socket:
                cd = clamd.ClamdUnixSocket(filename=clamav_socket)
                logger.info(f"ClamAV scanner initialized using socket: {clamav_socket}")
            else:
                cd = clamd.ClamdNetworkSocket(host=clamav_host, port=clamav_port)
                logger.info(f"ClamAV scanner initialized using host: {clamav_host}, port: {clamav_port}")

            # Check if ClamAV is running
            cd.ping()

            # Return ClamAV scanner instance if successful
            return cd

        except clamd.ConnectionError as e:
            logger.error(f"ClamAV daemon not found: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Failed to initialize ClamAV scanner: {str(e)}", exc_info=True)
            return None

    def _init_mock_scanner(self) -> Dict:
        """
        Initialize mock virus scanner for development/testing
        """
        # Create simple mock scanner object with scan method
        mock_scanner = {}

        # Configure mock behavior based on configuration
        mock_config = config.get_scanner_config()['mock']
        always_clean = mock_config['always_clean']
        scan_time = mock_config['scan_time']
        threat_detection_rate = mock_config['threat_detection_rate']

        # Set up mock virus signatures for testing
        mock_virus_signatures = ["VIRUS", "MALWARE", "TROJAN"]

        def scan(file_path):
            import time
            time.sleep(scan_time)
            with open(file_path, 'r') as f:
                content = f.read()
                for signature in mock_virus_signatures:
                    if signature in content:
                        return f"Mock Virus Found: {signature}"
            return None

        mock_scanner['scan'] = scan
        logger.info("Mock scanner initialized")
        return mock_scanner

    def _scan_with_clamav(self, file_path: str) -> Dict:
        """
        Scan a file using ClamAV virus scanner
        """
        # Check if ClamAV scanner is available
        if not self._scanner_instance:
            return {"status": ScanResult.ERROR.value, "details": "ClamAV scanner not initialized"}

        try:
            # Call instream scan method of ClamAV with file
            scan_result = self._scanner_instance.instream(file_path)

            # Parse ClamAV scan results
            if scan_result and scan_result['stream'][0][0] == 'OK':
                # Return CLEAN if no virus found
                return {"status": ScanResult.CLEAN.value, "details": "No threats found"}
            elif scan_result and scan_result['stream'][0][0] == 'FOUND':
                virus_name = scan_result['stream'][0][1]
                # Return INFECTED with virus name if virus found
                return {"status": ScanResult.INFECTED.value, "details": f"Virus found: {virus_name}"}
            else:
                return {"status": ScanResult.ERROR.value, "details": f"ClamAV scan failed: {scan_result}"}

        except Exception as e:
            # Handle exceptions and return ERROR with details
            logger.error(f"ClamAV scan error: {str(e)}", exc_info=True)
            return {"status": ScanResult.ERROR.value, "details": str(e)}

    def _scan_with_mock(self, file_path: str) -> Dict:
        """
        Scan a file using mock scanner for testing
        """
        try:
            # Read part of the file content to check against mock patterns
            with open(file_path, 'r') as f:
                content = f.read(1024)

            # Check if file contains mock virus signature
            if "VIRUS" in content:
                # Return INFECTED for files with 'VIRUS' in content or matching patterns
                return {"status": ScanResult.INFECTED.value, "details": "Mock virus signature found"}
            else:
                # Return CLEAN for all other files
                return {"status": ScanResult.CLEAN.value, "details": "No threats found (mock)"}

        except Exception as e:
            # Handle exceptions and return ERROR with details
            logger.error(f"Mock scan error: {str(e)}", exc_info=True)
            return {"status": ScanResult.ERROR.value, "details": str(e)}

    def _scan_with_custom(self, file_path: str) -> Dict:
        """
        Scan a file using custom scanner implementation
        """
        # Implement custom scanning logic
        # Potentially call external scanning tools via subprocess
        # Parse scan results and return appropriate ScanResult
        # Handle exceptions and tool-specific error codes
        return {"status": ScanResult.UNSUPPORTED.value, "details": "Custom scanner not implemented"}

    def verify_scanner_health(self) -> bool:
        """
        Check if the scanner is operational
        """
        # Check if scanner is enabled
        if not self._enabled:
            # If disabled, return True (considered healthy)
            self._is_healthy = True
            return True

        try:
            # If enabled, perform health check based on scanner type
            if self._scanner_type == 'clamav':
                if self._scanner_instance:
                    # Verify connection to daemon and version check
                    self._scanner_instance.ping()
                    self._is_healthy = True
                else:
                    self._is_healthy = False
            elif self._scanner_type == 'mock':
                # For mock scanner: always return True
                self._is_healthy = True
            else:
                # For custom scanner: perform custom health check
                self._is_healthy = False

        except Exception as e:
            # Handle exceptions and update health status
            self._is_healthy = False
            logger.error(f"Scanner health check failed: {str(e)}", exc_info=True)

        finally:
            # Update last health check timestamp and health status
            self._last_health_check = datetime.utcnow()
            logger.info(f"Scanner health check result: {self._is_healthy}")
            # Return health status boolean
            return self._is_healthy

    def get_scanner_stats(self) -> Dict:
        """
        Get statistics about the scanner operations
        """
        # Collect scanner type and configuration information
        stats = {
            "scanner_type": self._scanner_type,
            "enabled": self._enabled,
            "healthy": self._is_healthy,
            "last_health_check": self._last_health_check
        }

        try:
            # Gather operational statistics if available
            if self._scanner_type == 'clamav' and self._scanner_instance:
                # Get version, signature database date
                version = self._scanner_instance.version()
                stats["version"] = version
            elif self._scanner_type == 'mock':
                # Return mock statistics
                stats["version"] = "Mock Scanner"
            else:
                stats["version"] = "N/A"

        except Exception as e:
            logger.error(f"Error getting scanner stats: {str(e)}", exc_info=True)
            stats["error"] = str(e)

        # Return compiled statistics dictionary
        return stats

    def _cleanup_temp_files(self, file_path: str) -> bool:
        """
        Clean up temporary files used during scanning
        """
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"Temporary file not found: {file_path}")
            return True

        try:
            # Attempt to delete the temporary file
            os.remove(file_path)
            logger.debug(f"Deleted temporary file: {file_path}")
            # Return success status
            return True
        except Exception as e:
            # Handle exceptions if deletion fails
            logger.error(f"Error deleting temporary file: {str(e)}", exc_info=True)
            return False

    def _create_temp_directory(self) -> bool:
        """
        Create temporary directory for scan operations
        """
        # Check if temporary directory exists
        if os.path.exists(self._temp_directory):
            return True

        try:
            # Create directory if it doesn't exist
            os.makedirs(self._temp_directory, exist_ok=True)
            # Set proper permissions on directory
            os.chmod(self._temp_directory, 0o777)
            logger.debug(f"Created temporary directory: {self._temp_directory}")
            # Return success status
            return True
        except Exception as e:
            # Handle exceptions if creation fails
            logger.error(f"Error creating temporary directory: {str(e)}", exc_info=True)
            return False