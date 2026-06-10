'use client'

import { memo, useMemo, useState } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatPercent } from '@/lib/utils'

export interface CategoryChartDatum {
  name: string
  value: number
  count: number
  percentage: number
}

const CATEGORY_COLORS = ['#22c55e', '#38bdf8', '#f59e0b', '#f43f5e', '#a78bfa', '#14b8a6', '#f97316', '#e879f9']

function CategoryTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const item = payload[0].payload as CategoryChartDatum

  return (
    <div className="rounded-lg border border-border bg-card/95 px-3 py-2 text-sm shadow-xl backdrop-blur">
      <p className="font-semibold">{item.name}</p>
      <p className="text-muted-foreground">{formatCurrency(item.value, 'INR')}</p>
      <p className="text-xs text-muted-foreground">{item.count} transactions - {formatPercent(item.percentage / 100)}</p>
    </div>
  )
}

export const CategoryDonutChart = memo(function CategoryDonutChart({ data }: { data: CategoryChartDatum[] }) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)
  const total = useMemo(() => data.reduce((sum, item) => sum + item.value, 0), [data])
  const totalCount = useMemo(() => data.reduce((sum, item) => sum + item.count, 0), [data])

  return (
    <Card className="transition-all duration-300 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5">
      <CardHeader>
        <CardTitle>Spending by Category</CardTitle>
        <CardDescription>Final cleaned and AI-classified category mix</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(190px,0.9fr)]">
          <div className="relative h-[300px] min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius="58%"
                  outerRadius="82%"
                  paddingAngle={2}
                  cornerRadius={5}
                  dataKey="value"
                  animationBegin={80}
                  animationDuration={900}
                  onMouseEnter={(_, index) => setActiveIndex(index)}
                  onMouseLeave={() => setActiveIndex(null)}
                  labelLine={false}
                  label={false}
                >
                  {data.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                      stroke="hsl(var(--background))"
                      strokeWidth={2}
                      opacity={activeIndex === null || activeIndex === index ? 1 : 0.45}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CategoryTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-xs uppercase text-muted-foreground">Total spend</p>
              <p className="max-w-[150px] truncate text-center text-xl font-bold">{formatCurrency(total, 'INR')}</p>
              <p className="text-xs text-muted-foreground">{totalCount} txns</p>
            </div>
          </div>

          <div className="flex min-w-0 flex-col justify-center gap-2">
            {data.map((item, index) => (
              <div
                key={item.name}
                className="flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-accent/50"
                onMouseEnter={() => setActiveIndex(index)}
                onMouseLeave={() => setActiveIndex(null)}
              >
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[index % CATEGORY_COLORS.length] }} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{item.name}</p>
                  <p className="text-xs text-muted-foreground">{item.count} txns</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold">{formatPercent(item.percentage / 100)}</p>
                  <p className="text-xs text-muted-foreground">{formatCurrency(item.value, 'INR')}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
})
