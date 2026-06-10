'use client'

import { motion } from 'framer-motion'
import { Sparkles, Store, TriangleAlert } from 'lucide-react'
import type { JobSummary } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RiskBadge } from '@/components/dashboard/risk-badge'
import { formatCurrency } from '@/lib/utils'

export function AISummaryCard({ summary }: { summary: JobSummary }) {
  const sentences = summary.narrative
    ? summary.narrative.split(/(?<=[.!?])\s+/).filter(Boolean)
    : ['AI summary is not available for this job yet.']

  return (
    <Card className="glass overflow-hidden border-white/10 bg-card/70 shadow-xl shadow-black/10 transition-all duration-300 hover:border-primary/25">
      <CardHeader>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="flex items-center gap-3">
            <motion.span
              animate={{ rotate: [0, 8, -8, 0], scale: [1, 1.08, 1] }}
              transition={{ repeat: Infinity, repeatDelay: 4, duration: 1.4 }}
              className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10"
            >
              <Sparkles className="h-5 w-5 text-primary" />
            </motion.span>
            AI Narrative Summary
          </CardTitle>
          <RiskBadge risk={summary.risk_level} />
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-2">
          {sentences.map((sentence, index) => (
            <p key={index} className={index === 0 ? 'text-lg font-medium leading-relaxed' : 'text-sm leading-relaxed text-muted-foreground'}>
              {sentence}
            </p>
          ))}
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-border/60 bg-background/60 p-4">
            <div className="mb-2 flex items-center gap-2 text-xs uppercase text-muted-foreground">
              <TriangleAlert className="h-3.5 w-3.5" />
              Anomaly Insight
            </div>
            <p className="text-2xl font-bold">{summary.anomaly_count}</p>
            <p className="text-xs text-muted-foreground">transactions flagged</p>
          </div>

          <div className="rounded-lg border border-border/60 bg-background/60 p-4 md:col-span-2">
            <div className="mb-3 flex items-center gap-2 text-xs uppercase text-muted-foreground">
              <Store className="h-3.5 w-3.5" />
              Merchant Highlights
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              {(summary.top_merchants || []).slice(0, 3).map((item) => (
                <div key={item.merchant} className="min-w-0 rounded-md bg-accent/40 p-3">
                  <p className="truncate text-sm font-semibold">{item.merchant}</p>
                  <p className="text-xs text-muted-foreground">{formatCurrency(item.amount, 'INR')}</p>
                </div>
              ))}
              {(!summary.top_merchants || summary.top_merchants.length === 0) && (
                <p className="text-sm text-muted-foreground">No dominant merchants detected.</p>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
