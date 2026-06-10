'use client'

import { AlertTriangle, ShieldAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { Transaction } from '@/lib/types'
import { cn, formatCurrency, formatDate } from '@/lib/utils'

type Severity = 'Low' | 'Medium' | 'High'

function getSeverity(txn: Transaction): Severity {
  const reason = (txn.anomaly_reason || '').toLowerCase()
  if (reason.includes('3x') || txn.amount > 100000) return 'High'
  if (reason.includes('usd currency')) return 'Medium'
  return 'Low'
}

function severityClass(severity: Severity) {
  if (severity === 'High') return 'border-red-400/30 bg-red-500/10 text-red-200'
  if (severity === 'Medium') return 'border-amber-400/30 bg-amber-500/10 text-amber-100'
  return 'border-emerald-400/30 bg-emerald-500/10 text-emerald-100'
}

export function AnomalyTable({ anomalies }: { anomalies: Transaction[] }) {
  if (!anomalies.length) return null

  return (
    <Card className="border-red-500/20 transition-all duration-300 hover:border-red-500/30 hover:shadow-lg hover:shadow-red-500/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-red-400">
          <ShieldAlert className="h-5 w-5" />
          Detected Anomalies
        </CardTitle>
        <CardDescription>Suspicious or unusual transactions flagged for review</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="max-h-[380px] overflow-auto rounded-md border border-red-500/10">
          <Table>
            <TableHeader className="sticky top-0 z-10 bg-background">
              <TableRow>
                <TableHead>Severity</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Merchant</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Currency</TableHead>
                <TableHead>Reason</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {anomalies.map((txn) => {
                const severity = getSeverity(txn)
                return (
                  <TableRow key={txn.id} className="bg-red-500/[0.03] transition-colors hover:bg-red-500/[0.08]">
                    <TableCell>
                      <Badge variant="outline" className={cn('gap-1.5', severityClass(severity))}>
                        <AlertTriangle className="h-3 w-3" />
                        {severity}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(txn.date)}</TableCell>
                    <TableCell className="font-medium">{txn.merchant}</TableCell>
                    <TableCell className="font-bold">{formatCurrency(txn.amount, txn.currency)}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{txn.currency}</Badge>
                    </TableCell>
                    <TableCell className="min-w-[240px] text-sm text-red-200/90">{txn.anomaly_reason}</TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
