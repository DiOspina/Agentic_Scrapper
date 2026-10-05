import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from 'recharts'
import { cn } from '../../utils/helpers'

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

interface LineChartProps {
  data: Array<Record<string, any>>
  xKey: string
  lines: Array<{ key: string; name: string; color?: string; type?: 'line' | 'area' }>
  height?: number
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  animate?: boolean
  className?: string
}

export function LineChartComponent({
  data,
  xKey,
  lines,
  height = 300,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  animate = true,
  className,
}: LineChartProps) {
  if (!data.length) {
    return (
      <div className={cn('h-[300px] flex items-center justify-center', className)}>
        <p className="text-dark-500 dark:text-dark-400">No data available</p>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />}
        <XAxis
          dataKey={xKey}
          tick={{ fill: '#64748b', fontSize: 12 }}
          axisLine={{ stroke: '#e2e8f0' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#64748b', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          splitNumber={5}
        />
        {showTooltip && (
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
            }}
            labelStyle={{ color: '#f1f5f9', fontWeight: 600 }}
            itemStyle={{ fontSize: '13px' }}
            formatter={(value: number) => [value.toLocaleString(), '']}
          />
        )}
        {showLegend && <Legend wrapperStyle={{ paddingTop: 20 }} />}
        {lines.map((line, index) => (
          <Line
            key={line.key}
            type="monotone"
            dataKey={line.key}
            name={line.name}
            stroke={line.color || COLORS[index % COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6, strokeWidth: 2 }}
            animationDuration={animate ? 800 : 0}
            animationEasing="easeOutQuart"
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

interface AreaChartProps {
  data: Array<Record<string, any>>
  xKey: string
  areas: Array<{ key: string; name: string; color?: string; opacity?: number }>
  height?: number
  stacked?: boolean
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  className?: string
}

export function AreaChartComponent({
  data,
  xKey,
  areas,
  height = 300,
  stacked = false,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  className,
}: AreaChartProps) {
  if (!data.length) {
    return (
      <div className={cn('h-[300px] flex items-center justify-center', className)}>
        <p className="text-dark-500 dark:text-dark-400">No data available</p>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />}
        <XAxis
          dataKey={xKey}
          tick={{ fill: '#64748b', fontSize: 12 }}
          axisLine={{ stroke: '#e2e8f0' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#64748b', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        {showTooltip && (
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#f1f5f9', fontWeight: 600 }}
          />
        )}
        {showLegend && <Legend wrapperStyle={{ paddingTop: 20 }} />}
        {areas.map((area, index) => (
          <Area
            key={area.key}
            type="monotone"
            dataKey={area.key}
            name={area.name}
            stroke={area.color || COLORS[index % COLORS.length]}
            fill={area.color || COLORS[index % COLORS.length]}
            fillOpacity={area.opacity || 0.3}
            strokeWidth={2}
            stackId={stacked ? 'stack' : undefined}
            animationDuration={800}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}

interface BarChartProps {
  data: Array<Record<string, any>>
  xKey: string
  bars: Array<{ key: string; name: string; color?: string }>
  height?: number
  horizontal?: boolean
  stacked?: boolean
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  showValue?: boolean
  className?: string
}

export function BarChartComponent({
  data,
  xKey,
  bars,
  height = 300,
  horizontal = false,
  stacked = false,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  showValue = false,
  className,
}: BarChartProps) {
  if (!data.length) {
    return (
      <div className={cn('h-[300px] flex items-center justify-center', className)}>
        <p className="text-dark-500 dark:text-dark-400">No data available</p>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout={horizontal ? 'vertical' : 'horizontal'} margin={{ top: 10, right: 20, left: horizontal ? 80 : 0, bottom: horizontal ? 0 : 20 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={!horizontal} horizontal={horizontal} />}
        {horizontal ? (
          <YAxis
            type="category"
            dataKey={xKey}
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={{ stroke: '#e2e8f0' }}
            tickLine={false}
            width={80}
          />
        ) : (
          <XAxis
            dataKey={xKey}
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={{ stroke: '#e2e8f0' }}
            tickLine={false}
          />
        )}
        {horizontal ? (
          <XAxis
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
        ) : (
          <YAxis
            tick={{ fill: '#64748b', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
        )}
        {showTooltip && (
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#f1f5f9', fontWeight: 600 }}
          />
        )}
        {showLegend && <Legend wrapperStyle={{ paddingTop: 20 }} />}
        {bars.map((bar, index) => (
          <Bar
            key={bar.key}
            dataKey={bar.key}
            name={bar.name}
            fill={bar.color || COLORS[index % COLORS.length]}
            radius={[4, 4, 0, 0]}
            stackId={stacked ? 'stack' : undefined}
            maxBarSize={40}
          >
            {showValue && data.map((entry, i) => (
              <Cell key={i} fill={bar.color || COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

interface PieChartProps {
  data: Array<{ name: string; value: number; color?: string }>
  height?: number
  innerRadius?: number
  outerRadius?: number
  showLegend?: boolean
  showTooltip?: boolean
  showLabels?: boolean
  className?: string
}

export function PieChartComponent({
  data,
  height = 300,
  innerRadius = 60,
  outerRadius = 100,
  showLegend = true,
  showTooltip = true,
  showLabels = true,
  className,
}: PieChartProps) {
  if (!data.length) {
    return (
      <div className={cn('h-[300px] flex items-center justify-center', className)}>
        <p className="text-dark-500 dark:text-dark-400">No data available</p>
      </div>
    )
  }

  const total = data.reduce((sum, item) => sum + item.value, 0)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          paddingAngle={2}
          dataKey="value"
          nameKey="name"
          label={showLabels ? ({ name, value, percent }) => (
            <span className="text-sm font-medium text-dark-900 dark:text-white">
              {name}: {(percent * 100).toFixed(1)}%
            </span>
          ) : false}
          labelLine={showLabels}
        >
          {data.map((item, index) => (
            <Cell key={`cell-${index}`} fill={item.color || COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        {showTooltip && (
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#f1f5f9', fontWeight: 600 }}
            formatter={(value: number) => [value.toLocaleString(), '']}
          />
        )}
        {showLegend && <Legend wrapperStyle={{ paddingTop: 20 }} />}
      </PieChart>
    </ResponsiveContainer>
  )
}

interface ComposedChartProps {
  data: Array<Record<string, any>>
  xKey: string
  lines?: Array<{ key: string; name: string; color?: string }>
  bars?: Array<{ key: string; name: string; color?: string }>
  areas?: Array<{ key: string; name: string; color?: string; opacity?: number }>
  height?: number
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  className?: string
}

export function ComposedChartComponent({
  data,
  xKey,
  lines = [],
  bars = [],
  areas = [],
  height = 300,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  className,
}: ComposedChartProps) {
  if (!data.length) {
    return (
      <div className={cn('h-[300px] flex items-center justify-center', className)}>
        <p className="text-dark-500 dark:text-dark-400">No data available</p>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />}
        <XAxis
          dataKey={xKey}
          tick={{ fill: '#64748b', fontSize: 12 }}
          axisLine={{ stroke: '#e2e8f0' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#64748b', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        {showTooltip && (
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#f1f5f9', fontWeight: 600 }}
          />
        )}
        {showLegend && <Legend wrapperStyle={{ paddingTop: 20 }} />}
        {areas.map((area, index) => (
          <Area
            key={area.key}
            type="monotone"
            dataKey={area.key}
            name={area.name}
            stroke={area.color || COLORS[index % COLORS.length]}
            fill={area.color || COLORS[index % COLORS.length]}
            fillOpacity={area.opacity || 0.2}
            strokeWidth={2}
            animationDuration={800}
          />
        ))}
        {bars.map((bar, index) => (
          <Bar
            key={bar.key}
            dataKey={bar.key}
            name={bar.name}
            fill={bar.color || COLORS[(index + areas.length) % COLORS.length]}
            radius={[4, 4, 0, 0]}
            maxBarSize={40}
          />
        ))}
        {lines.map((line, index) => (
          <Line
            key={line.key}
            type="monotone"
            dataKey={line.key}
            name={line.name}
            stroke={line.color || COLORS[(index + areas.length + bars.length) % COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6, strokeWidth: 2 }}
            animationDuration={800}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  )
}