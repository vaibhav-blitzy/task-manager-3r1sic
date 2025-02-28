import React, { useEffect, useMemo } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, ChartOptions, ChartData } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { useTheme } from '../../../../contexts/ThemeContext';
import { useMediaQuery } from '../../../../hooks/useMediaQuery';

// Register required Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

export interface PieChartProps {
  /** Array of data points to visualize */
  data: Array<{label: string, value: number, color?: string}>;
  /** Chart title */
  title?: string;
  /** Text to display in the center (for donut charts only) */
  centerText?: string;
  /** Chart height */
  height?: number | string;
  /** Chart width */
  width?: number | string;
  /** Additional CSS classes */
  className?: string;
  /** Whether to show the legend */
  showLegend?: boolean;
  /** Whether to show tooltips on hover */
  showTooltips?: boolean;
  /** Whether to show labels on chart segments */
  showLabels?: boolean;
  /** Whether to render as a donut chart */
  donut?: boolean;
  /** Optional custom colors array (if not provided, will use theme or default colors) */
  colors?: string[];
  /** Click handler for chart segments */
  onClick?: (index: number) => void;
}

/**
 * A component that renders a pie or donut chart using Chart.js to visualize proportional data.
 * Used for task status distribution, project completion rates, and other metrics.
 */
const PieChart: React.FC<PieChartProps> = ({
  data,
  title,
  centerText,
  height = 300,
  width = '100%',
  className = '',
  showLegend = true,
  showTooltips = true,
  showLabels = false,
  donut = false,
  colors,
  onClick
}) => {
  // Access theme colors
  const { colors: themeColors } = useTheme();
  
  // Use responsive sizing
  const isMobile = useMediaQuery('(max-width: 640px)');
  
  // Adjust dimensions for mobile
  const chartHeight = isMobile ? (typeof height === 'number' ? height * 0.8 : 240) : height;
  const chartWidth = width;
  
  // Default color palette from theme if not provided
  const chartColors = useMemo(() => {
    if (colors && colors.length > 0) {
      return colors;
    }
    
    // Use theme colors or fallback to predefined colors
    return [
      themeColors.primary,
      themeColors.secondary,
      themeColors.success,
      themeColors.warning,
      themeColors.error,
      '#6366F1', // Indigo
      '#14B8A6', // Teal
      '#F97316', // Orange
      '#8B5CF6', // Purple
      '#EC4899'  // Pink
    ];
  }, [colors, themeColors]);
  
  // Transform data for Chart.js
  const chartData: ChartData<'pie'> = useMemo(() => {
    return {
      labels: data.map(item => item.label),
      datasets: [{
        data: data.map(item => item.value),
        backgroundColor: data.map((item, index) => 
          item.color || chartColors[index % chartColors.length]
        ),
        borderColor: themeColors.background.primary,
        borderWidth: 2,
      }]
    };
  }, [data, chartColors, themeColors]);
  
  // Chart options
  const chartOptions: ChartOptions<'pie'> = useMemo(() => {
    let options: ChartOptions<'pie'> = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: showLegend,
          position: 'bottom',
          labels: {
            color: themeColors.text.primary,
            font: {
              size: isMobile ? 10 : 12
            },
            padding: 20,
            usePointStyle: true,
          }
        },
        tooltip: {
          enabled: showTooltips,
          backgroundColor: themeColors.background.secondary,
          titleColor: themeColors.text.primary,
          bodyColor: themeColors.text.primary,
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 13
          },
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: (context) => {
              const label = context.label || '';
              const value = context.raw as number;
              const total = context.dataset.data.reduce((sum, val) => sum + (val as number), 0);
              const percentage = Math.round((value / total) * 100);
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        },
        title: {
          display: !!title,
          text: title || '',
          color: themeColors.text.primary,
          font: {
            size: isMobile ? 14 : 16,
            weight: 'bold'
          },
          padding: {
            top: 10,
            bottom: 20
          }
        }
      },
      elements: {
        arc: {
          borderWidth: 1,
        }
      },
      layout: {
        padding: 10
      },
      animation: {
        animateRotate: true,
        animateScale: true,
        duration: 800,
        easing: 'easeOutQuart'
      }
    };
    
    // Configure for donut chart if needed
    if (donut) {
      options = {
        ...options,
        cutout: '70%'
      };
      
      // Add center text if provided
      if (centerText) {
        options.plugins = {
          ...options.plugins,
          // Center text requires the 'tooltip' plugin to be present
          // This will be attached through the afterDraw hook
        };
      }
    }
    
    return options;
  }, [showLegend, showTooltips, title, donut, centerText, themeColors, isMobile]);
  
  // Add center text to donut chart
  useEffect(() => {
    if (donut && centerText) {
      const originalDraw = ChartJS.overrides.pie.plugins.legend.afterDraw;
      
      ChartJS.overrides.pie.plugins.legend.afterDraw = (chart) => {
        if (originalDraw) {
          originalDraw(chart);
        }
        
        const { ctx, width, height } = chart;
        const fontSize = isMobile ? 14 : 16;
        ctx.save();
        ctx.font = `bold ${fontSize}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = themeColors.text.primary;
        ctx.fillText(centerText, width / 2, height / 2);
        ctx.restore();
      };
      
      return () => {
        ChartJS.overrides.pie.plugins.legend.afterDraw = originalDraw;
      };
    }
  }, [donut, centerText, themeColors, isMobile]);
  
  // Handle click events
  const handleClick = (event: any, elements: any) => {
    if (onClick && elements.length > 0) {
      onClick(elements[0].index);
    }
  };
  
  // Accessibility attributes
  const accessibilityProps = {
    role: 'img',
    'aria-label': title || 'Pie chart showing data distribution',
  };
  
  return (
    <div 
      className={`pie-chart ${className}`} 
      style={{ height: chartHeight, width: chartWidth }}
      {...accessibilityProps}
    >
      <Pie 
        data={chartData}
        options={chartOptions}
        onClick={onClick ? handleClick : undefined}
      />
    </div>
  );
};

export default PieChart;