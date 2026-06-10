'use client'

import { useEffect, useState, useMemo } from 'react'
import { useParams } from 'next/navigation'
import { getJobStatus, getJobResults } from '@/lib/api'
import type { Job, JobResults, Transaction } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { RiskBadge } from '@/components/ui/risk-badge'
import { Loader2, TrendingUp, AlertTriangle, DollarSign, BarChart3, Search, Download, ArrowUpDown, Sparkles, ShieldAlert, Activity } from 'lucide-react'
import { formatCurrency, formatDate, downloadCSV, getAnomalySeverity, getSeverityColor } from '@/lib/utils'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { motion } from 'framer-motion'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6']

export default function ResultsPage() {
  const params = useParams()
  const jobId = parseInt(params.id as string)
  
  const [job, setJob] = useState<Job | null>(null)
  const [results, setResults] = useState<JobResults | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortField, setSortField] = useState<'date' | 'amount' | 'merchant'>('date')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const jobStatus = await getJobStatus(jobId)
        setJob(jobStatus)

        if (jobStatus.status === 'completed') {
          const jobResults = await getJobResults(jobId)
          setResults(jobResults)
          setLoading(false)
        } else if (jobStatus.status === 'failed') {
          setError(jobStatus.error_message || 'Processing failed')
          setLoading(false)
        } else {
          setTimeout(pollStatus, 3000)
        }
      } catch (err: any) {
        setError('Failed to fetch job status')
        setLoading(false)
      }
    }

    pollStatus()
  }, [jobId])

  // Calculate totals from transactions if summary is null
  const calculatedTotals = useMemo(() => {
    if (!results?.transactions) return { inr: 0, usd: 0, other: 0 }
    
    return results.transactions.reduce((acc, txn) => {
      if (txn.currency === 'INR') {
        acc.inr += txn.amount
      } else if (txn.currency === 'USD') {
        acc.usd += txn.amount
      } else {
        acc.other += txn.amount
      }
      return acc
    }, { inr: 0, usd: 0, other: 0 })
  }, [results])

  // Prepare chart data (DONUT CHART with better formatting)
  const categoryChartData = useMemo(() => {
    if (!results?.category_breakdown) return []
    return results.category_breakdown
      .filter(cat => cat.total_amount > 0)
      .map(cat => ({
        name: cat.category || 'Uncategorized',
        value: cat.total_amount,
        count: cat.count
      }))
      .sort((a, b) => b.value - a.value)
  }, [results])

  const topMerchantsData = useMemo(() => {
    if (!results?.transactions) return []
    
    const merchantTotals = results.transactions.reduce((acc: any, txn) => {
      const merchant = txn.merchant || 'Unknown'
      if (!acc[merchant]) {
        acc[merchant] = 0
      }
      acc[merchant] += txn.amount
      return acc
    }, {})

    return Object.entries(merchantTotals)
      .sort(([, a]: any, [, b]: any) => b - a)
      .slice(0, 10)
      .map(([merchant, amount]) => ({ merchant, amount }))
  }, [results])

  // Filter and sort transactions
  const filteredTransactions = useMemo(() => {
    if (!results?.transactions) return []
    
    let filtered = results.transactions.filter(txn => 
      txn.merchant?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.category?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.txn_id?.toLowerCase().includes(searchQuery.toLowerCase())
    )

    filtered.sort((a, b) => {
      let comparison = 0
      if (sortField === 'date') {
        comparison = new Date(a.date).getTime() - new Date(b.date).getTime()
      } else if (sortField === 'amount') {
        comparison = a.amount - b.amount
      } else if (sortField === 'merchant') {
        comparison = (a.merchant || '').localeCompare(b.merchant || '')
      }
      return sortDirection === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [results, searchQuery, sortField, sortDirection])

  const toggleSort = (field: 'date' | 'amount' | 'merchant') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  // Custom label for donut chart - positioned outside to avoid overlap
  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }: any) => {
    if (percent < 0.05) return null // Hide labels for very small slices
    
    const RADIAN = Math.PI / 180
    const radius = outerRadius + 25 // Position outside the chart
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    return (
      <text
        x={x}
        y={y}
        fill="currentColor"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-xs font-medium"
      >
        {`${name}: ${(percent * 100).toFixed(0)}%`}
      </text>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-7xl mx-auto">
          <Card>
            <CardContent className="p-12 text-center">
              <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-primary" />
              <h2 className="text-2xl font-bold mb-2">Processing Your Data</h2>
              <p className="text-muted-foreground mb-4">
                Status: {job?.status || 'Loading...'}
              </p>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>✓ Uploading</p>
                <p>⟳ Cleaning Data</p>
                <p>⟳ Detecting Anomalies</p>
                <p>⟳ AI Classification</p>
                <p>⟳ Generating Summary</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-7xl mx-auto">
          <Card>
            <CardContent className="p-12 text-center">
              <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-destructive" />
              <h2 className="text-2xl font-bold mb-2 text-destructive">Error</h2>
              <p className="text-muted-foreground">{error}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const inrTotal = results?.summary?.total_spend_inr ?? calculatedTotals.inr
  const usdTotal = results?.summary?.total_spend_usd ?? calculatedTotals.usd
  const totalAmount = categoryChartData.reduce((sum, cat) => sum + cat.value, 0)

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold mb-2">Transaction Analysis</h1>
              <p className="text-muted-foreground">
                Job #{jobId} • {results?.filename} • {results?.transactions.length} transactions
              </p>
            </div>
            <Button 
              onClick={() => results && downloadCSV(results.transactions, `transactions-${jobId}.csv`)}
              variant="outline"
              className="gap-2"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </Button>
          </div>
        </motion.div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-500" />
                  <p className="text-2xl md:text-3xl font-bold">
                    {results?.transactions.length || 0}
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">INR Spend</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-green-500" />
                  <p className="text-2xl md:text-3xl font-bold truncate">
                    {formatCurrency(inrTotal, 'INR')}
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">USD Spend</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-purple-500" />
                  <p className="text-2xl md:text-3xl font-bold truncate">
                    {formatCurrency(usdTotal, 'USD')}
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Anomalies</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <p className="text-2xl md:text-3xl font-bold text-red-500">
                    {results?.anomalies.length || 0}
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* AI Summary - PREMIUM CARD */}
        {results?.summary?.narrative && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-background to-background backdrop-blur-sm hover:shadow-xl transition-all">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <motion.div
                      animate={{ rotate: [0, 10, -10, 0] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                      className="p-2 bg-primary/10 rounded-lg"
                    >
                      <Sparkles className="w-6 h-6 text-primary" />
                    </motion.div>
                    <div>
                      <CardTitle className="text-xl">AI-Powered Insights</CardTitle>
                      <CardDescription>Gemini analysis of your spending patterns</CardDescription>
                    </div>
                  </div>
                  <RiskBadge level={results.summary.risk_level} />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Narrative */}
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p className="text-base leading-relaxed">{results.summary.narrative}</p>
                </div>

                {/* Key Metrics */}
                <div className="grid md:grid-cols-2 gap-4 pt-4 border-t">
                  <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                    <Activity className="w-5 h-5 text-blue-500" />
                    <div>
                      <p className="text-xs text-muted-foreground">Anomalies Detected</p>
                      <p className="text-lg font-bold">{results.summary.anomaly_count}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-green-500" />
                    <div>
                      <p className="text-xs text-muted-foreground">Top Merchant</p>
                      <p className="text-lg font-bold truncate">
                        {topMerchantsData[0]?.merchant || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Charts Section */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* DONUT CHART - Improved */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle>Spending by Category</CardTitle>
                <CardDescription>Distribution of expenses across categories</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ResponsiveContainer width="100%" height={400}>
                  <PieChart>
                    <Pie
                      data={categoryChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={true}
                      label={renderCustomLabel}
                      outerRadius={130}
                      innerRadius={85}
                      fill="#8884d8"
                      dataKey="value"
                      animationBegin={0}
                      animationDuration={800}
                    >
                      {categoryChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: any) => formatCurrency(value, 'INR')}
                      contentStyle={{
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        border: 'none',
                        borderRadius: '8px',
                        padding: '8px 12px'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                {/* Center Label - below the chart */}
                <div className="text-center py-4 border-t">
                  <p className="text-3xl font-bold mb-1">{formatCurrency(totalAmount, 'INR')}</p>
                  <p className="text-sm text-muted-foreground">Total Spend</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Top Merchants Bar Chart */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle>Top Merchants</CardTitle>
                <CardDescription>Highest spending merchants</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={topMerchantsData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                    <XAxis
                      dataKey="merchant"
                      angle={-45}
                      textAnchor="end"
                      height={100}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip
                      formatter={(value: any) => formatCurrency(value, 'INR')}
                      contentStyle={{
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        border: 'none',
                        borderRadius: '8px',
                        padding: '8px 12px'
                      }}
                    />
                    <Bar
                      dataKey="amount"
                      fill="#3b82f6"
                      radius={[8, 8, 0, 0]}
                      animationBegin={0}
                      animationDuration={800}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Anomalies Section - IMPROVED WITH SEVERITY */}
        {results && results.anomalies.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.8 }}
          >
            <Card className="border-red-500/20 hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-red-500" />
                  <div>
                    <CardTitle className="text-red-500">Detected Anomalies</CardTitle>
                    <CardDescription>Suspicious or unusual transactions flagged for review</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader className="sticky top-0 bg-background z-10">
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
                      {results.anomalies.map((txn) => {
                        const severity = getAnomalySeverity(txn.anomaly_reason)
                        return (
                          <TableRow key={txn.id} className="bg-red-500/5 hover:bg-red-500/10 transition-colors">
                            <TableCell>
                              <Badge variant="outline" className={getSeverityColor(severity)}>
                                {severity.toUpperCase()}
                              </Badge>
                            </TableCell>
                            <TableCell>{formatDate(txn.date)}</TableCell>
                            <TableCell className="font-medium">{txn.merchant}</TableCell>
                            <TableCell className="font-bold">{formatCurrency(txn.amount, txn.currency)}</TableCell>
                            <TableCell>
                              <Badge variant="outline">{txn.currency}</Badge>
                            </TableCell>
                            <TableCell className="text-red-600 text-sm">{txn.anomaly_reason}</TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* All Transactions Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.9 }}
        >
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle>All Transactions</CardTitle>
              <CardDescription>Complete transaction history with search and sort</CardDescription>
              <div className="flex items-center gap-4 mt-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search transactions..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <p className="text-sm text-muted-foreground">
                  {filteredTransactions.length} of {results?.transactions.length} transactions
                </p>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader className="sticky top-0 bg-background z-10">
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>
                        <Button variant="ghost" size="sm" onClick={() => toggleSort('date')} className="gap-1 -ml-3">
                          Date
                          <ArrowUpDown className="w-3 h-3" />
                        </Button>
                      </TableHead>
                      <TableHead>
                        <Button variant="ghost" size="sm" onClick={() => toggleSort('merchant')} className="gap-1 -ml-3">
                          Merchant
                          <ArrowUpDown className="w-3 h-3" />
                        </Button>
                      </TableHead>
                      <TableHead>
                        <Button variant="ghost" size="sm" onClick={() => toggleSort('amount')} className="gap-1 -ml-3">
                          Amount
                          <ArrowUpDown className="w-3 h-3" />
                        </Button>
                      </TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Account</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTransactions.slice(0, 100).map((txn) => (
                      <TableRow
                        key={txn.id}
                        className={`${txn.is_anomaly ? 'bg-red-500/5 hover:bg-red-500/10' : 'hover:bg-muted/50'} transition-colors`}
                      >
                        <TableCell className="font-mono text-xs">{txn.txn_id}</TableCell>
                        <TableCell className="text-sm">{formatDate(txn.date)}</TableCell>
                        <TableCell className="font-medium">{txn.merchant}</TableCell>
                        <TableCell className="font-bold">
                          {formatCurrency(txn.amount, txn.currency)}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{txn.category || 'Uncategorized'}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={txn.status === 'SUCCESS' ? 'default' : 'destructive'}>
                            {txn.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">{txn.account_id}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {filteredTransactions.length > 100 && (
                  <div className="text-center py-4 text-sm text-muted-foreground">
                    Showing first 100 transactions. Use search to filter results.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
