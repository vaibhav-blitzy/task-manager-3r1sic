import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { useTheme } from '../../../../contexts/ThemeContext';
import { useMediaQuery } from '../../../../hooks/useMediaQuery';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartProps {
  data: Array<{label: string, value: number, color?: string}>;
  title?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number | string;
  width?: number | string;
  showLegend?: boolean;
  horizontal?: boolean;
  className?: string;
  onClick?: (index: number) => void;
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  title = '',
  xAxisLabel = '',
  yAxisLabel = '',
  height = 300,
  width = '100%',
  showLegend = true,
  horizontal = false,
  className = '',
  onClick
}) => {
  const { colors } = useTheme();
  const isMobile = useMediaQuery('(max-width: 640px)');
  
  // Default colors for bars when not provided
  const chartColors = [
    colors.primary,
    colors.secondary,
    colors.success,
    colors.warning,
    colors.error,
  ];
  
  // Transform input data to Chart.js format
  const chartData: ChartData<'bar'> = {
    labels: data.map(item => item.label),
    datasets: [
      {
        data: data.map(item => item.value),
        backgroundColor: data.map((item, index) => 
          item.color || chartColors[index % chartColors.length]
        ),
        borderColor: colors.background.primary,
        borderWidth: 1,
        barPercentage: 0.7,
        categoryPercentage: 0.8,
      }
    ]
  };

  // Chart options
  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: horizontal ? 'y' : 'x',
    plugins: {
      legend: {
        display: showLegend,
        position: 'top',
        labels: {
          color: colors.text.primary,
          font: {
            size: isMobile ? 12 : 14,
          }
        }
      },
      title: {
        display: !!title,
        text: title,
        color: colors.text.primary,
        font: {
          size: isMobile ? 14 : 16,
          weight: 'bold',
        },
        padding: {
          top: 10,
          bottom: 20
        }
      },
      tooltip: {
        backgroundColor: colors.background.secondary,
        titleColor: colors.text.primary,
        bodyColor: colors.text.primary,
        borderColor: colors.neutral[200],
        borderWidth: 1,
        padding: 10,
      }
    },
    scales: {
      x: {
        title: {
          display: !!xAxisLabel,
          text: xAxisLabel,
          color: colors.text.secondary,
          font: {
            size: isMobile ? 12 : 14,
          },
        },
        ticks: {
          color: colors.text.secondary,
          font: {
            size: isMobile ? 10 : 12,
          },
          maxRotation: horizontal ? 0 : 45,
        },
        grid: {
          color: colors.neutral[200],
        },
      },
      y: {
        title: {
          display: !!yAxisLabel,
          text: yAxisLabel,
          color: colors.text.secondary,
          font: {
            size: isMobile ? 12 : 14,
          },
        },
        ticks: {
          color: colors.text.secondary,
          font: {
            size: isMobile ? 10 : 12,
          },
        },
        grid: {
          color: colors.neutral[200],
        },
        beginAtZero: true,
      }
    },
    onClick: (_, elements) => {
      if (onClick && elements.length > 0) {
        onClick(elements[0].index);
      }
    },
    animation: {
      duration: 500,
    },
  };

  // Handle empty data case
  if (data.length === 0) {
    return (
      <div 
        className={`bar-chart-container ${className}`} 
        style={{ 
          height, 
          width, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          backgroundColor: colors.background.secondary,
          color: colors.text.secondary,
          borderRadius: '4px'
        }}
      >
        No data available to display
      </div>
    );
  }

  // Accessibility attributes
  const ariaLabel = `Bar chart ${title ? 'titled ' + title : ''} with ${data.length} data points`;

  return (
    <div
      className={`bar-chart-container ${className}`}
      style={{ height, width }}
      aria-label={ariaLabel}
    >
      <Bar data={chartData} options={options} />
    </div>
  );
};