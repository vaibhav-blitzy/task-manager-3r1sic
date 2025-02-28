import React from 'react';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  TimeScale, 
  Title, 
  Tooltip, 
  Legend, 
  ChartOptions,
  ChartData
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { adapters } from 'chart.js';
import DateAdapter from 'chartjs-adapter-date-fns';

import { useTheme } from '../../../../contexts/ThemeContext';
import { useMediaQuery } from '../../../../hooks/useMediaQuery';
import { formatDate } from '../../../../utils/date';

// Register required Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  TimeScale,
  Title,
  Tooltip,
  Legend
);

// Set up adapter for time-based charts
adapters.setDateAdapter(DateAdapter);

interface LineChartProps {
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
    tension?: number;
  }>;
  labels: string[] | Date[];
  title?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  xAxisType?: 'category' | 'time';
  height?: number | string;
  width?: number | string;
  className?: string;
  showGridLines?: boolean;
  showLegend?: boolean;
  showTooltips?: boolean;
  colors?: string[];
  onClick?: (index: number) => void;
}

/**
 * A component that renders a line chart using Chart.js to visualize trend data over time or categories.
 * Supports time-series or category-based visualizations for tracking trends, task completion,
 * burndown charts, and activity metrics in the Task Management System.
 * 
 * @param props - The component props
 * @returns The rendered line chart component
 */
const LineChart: React.FC<LineChartProps> = ({
  datasets,
  labels,
  title,
  xAxisLabel,
  yAxisLabel,
  xAxisType = 'category',
  height,
  width,
  className = '',
  showGridLines = true,
  showLegend = true,
  showTooltips = true,
  colors,
  onClick,
}) => {
  // Get theme colors and responsive breakpoints
  const { colors: themeColors } = useTheme();
  const isMobile = useMediaQuery('(max-width: 640px)');
  const isTablet = useMediaQuery('(min-width: 641px) and (max-width: 1024px)');

  // Default colors from theme if not provided via props
  const defaultColors = [
    themeColors.primary,
    themeColors.secondary,
    themeColors.success,
    themeColors.warning,
    themeColors.error,
  ];

  // Process datasets with consistent styling and colors
  const processedDatasets = datasets.map((dataset, index) => {
    // Use provided color or fall back to theme colors in sequence
    const lineColor = dataset.borderColor || colors?.[index] || defaultColors[index % defaultColors.length];
    
    // Create semi-transparent background based on line color
    const bgColor = dataset.backgroundColor || `${lineColor}20`; // 20 = 12.5% opacity
    
    return {
      ...dataset,
      borderColor: lineColor,
      backgroundColor: bgColor,
      tension: dataset.tension ?? 0.3,
      pointBackgroundColor: lineColor,
      pointBorderColor: themeColors.background.primary,
      pointHoverBackgroundColor: themeColors.background.primary,
      pointHoverBorderColor: lineColor,
      pointRadius: isMobile ? 2 : 3,
      pointHoverRadius: isMobile ? 3 : 5,
      borderWidth: isMobile ? 2 : 3,
    };
  });

  // Determine chart dimensions based on props or screen size
  const chartHeight = height || (isMobile ? 200 : isTablet ? 300 : 400);
  const chartWidth = width || '100%';

  // Configure chart options based on props and responsive state
  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    
    // Plugin configuration (title, legend, tooltip)
    plugins: {
      title: {
        display: !!title,
        text: title || '',
        color: themeColors.text.primary,
        font: {
          size: isMobile ? 14 : 16,
          weight: 'bold',
        },
        padding: {
          top: 10,
          bottom: 20,
        },
      },
      legend: {
        display: showLegend,
        position: isMobile ? 'bottom' : 'top',
        labels: {
          color: themeColors.text.primary,
          usePointStyle: true,
          pointStyle: 'circle',
          padding: isMobile ? 10 : 15,
          font: {
            size: isMobile ? 10 : 12,
          },
        },
      },
      tooltip: {
        enabled: showTooltips,
        backgroundColor: themeColors.background.secondary,
        titleColor: themeColors.text.primary,
        bodyColor: themeColors.text.secondary,
        borderColor: themeColors.neutral[200],
        borderWidth: 1,
        padding: isMobile ? 8 : 10,
        cornerRadius: 4,
        displayColors: true,
        callbacks: {
          // Format the tooltip label (dataset name and value)
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            return `${label}: ${value}`;
          },
          // Format the tooltip title (x-axis value)
          title: (tooltipItems) => {
            if (!tooltipItems.length) return '';
            
            const index = tooltipItems[0].dataIndex;
            if (index >= labels.length) return '';
            
            const label = labels[index];
            
            // Format date labels differently
            if (xAxisType === 'time' && label instanceof Date) {
              return formatDate(label);
            }
            
            return String(label || '');
          },
        },
      },
    },
    
    // Configure the X and Y axes
    scales: {
      x: {
        type: xAxisType,
        title: {
          display: !!xAxisLabel,
          text: xAxisLabel || '',
          color: themeColors.text.primary,
          padding: { top: 10 },
          font: {
            size: isMobile ? 10 : 12,
          },
        },
        grid: {
          display: showGridLines,
          color: themeColors.neutral[200] + '40', // 40 = 25% opacity
          drawBorder: true,
          borderColor: themeColors.neutral[200],
        },
        ticks: {
          color: themeColors.text.secondary,
          font: {
            size: isMobile ? 8 : 10,
          },
          maxRotation: isMobile ? 45 : 0,
          callback: (value, index) => {
            // Catch out of bounds index
            if (index >= labels.length) return '';
            
            if (xAxisType === 'time') {
              // For time axis, format date appropriately
              try {
                const date = new Date(value as number);
                return formatDate(date, isMobile ? 'MMM d' : 'MMM d, yyyy');
              } catch (error) {
                return '';
              }
            }
            
            // For category axis, truncate long labels on mobile
            const label = String(labels[index] || '');
            if (isMobile && label.length > 8) {
              return label.substring(0, 8) + '...';
            }
            return label;
          },
        },
        // Additional configuration for time axis
        ...(xAxisType === 'time' ? {
          time: {
            unit: 'day',
            tooltipFormat: 'MMM d, yyyy',
            displayFormats: {
              day: isMobile ? 'MMM d' : 'MMM d, yyyy',
            },
          },
          adapters: {
            date: {
              locale: 'en-US',
            },
          },
        } : {}),
      },
      y: {
        beginAtZero: true,
        title: {
          display: !!yAxisLabel,
          text: yAxisLabel || '',
          color: themeColors.text.primary,
          padding: { bottom: 10 },
          font: {
            size: isMobile ? 10 : 12,
          },
        },
        grid: {
          display: showGridLines,
          color: themeColors.neutral[200] + '40', // 25% opacity
          drawBorder: true,
          borderColor: themeColors.neutral[200],
        },
        ticks: {
          color: themeColors.text.secondary,
          font: {
            size: isMobile ? 8 : 10,
          },
        },
      },
    },
    
    // Interaction settings
    interaction: {
      mode: 'index',
      intersect: false,
    },
    
    // Animation settings
    animation: {
      duration: 500,
    },
    
    // Line element styling
    elements: {
      line: {
        tension: 0.3,
      },
    },
  };

  // Add click handler if provided
  if (onClick) {
    options.onClick = (event, elements) => {
      if (elements.length > 0) {
        onClick(elements[0].index);
      }
    };
  }

  // Prepare data for the chart
  const data: ChartData<'line'> = {
    labels,
    datasets: processedDatasets,
  };

  // Check if there is data to display
  const hasData = datasets.length > 0 && datasets.some(dataset => dataset.data.length > 0);

  if (!hasData) {
    return (
      <div 
        className={`line-chart-container ${className}`} 
        style={{ 
          height: chartHeight, 
          width: chartWidth,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: themeColors.background.secondary,
          borderRadius: '4px',
          color: themeColors.text.secondary
        }}
      >
        No data available to display
      </div>
    );
  }

  return (
    <div 
      className={`line-chart-container ${className}`} 
      style={{ height: chartHeight, width: chartWidth }}
      aria-label={title || 'Line chart'}
      role="img"
    >
      <Line
        data={data}
        options={options}
        aria-label={title || 'Line chart'}
      />
    </div>
  );
};

export default LineChart;