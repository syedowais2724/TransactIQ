'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, TrendingUp, AlertCircle, FileText } from 'lucide-react'
import Link from 'next/link'

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome to your AI-powered transaction analytics platform
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          <QuickActionCard
            title="Upload CSV"
            description="Process new transactions"
            icon={<Upload className="w-6 h-6" />}
            href="/dashboard/upload"
          />
          <QuickActionCard
            title="View Jobs"
            description="Check processing status"
            icon={<FileText className="w-6 h-6" />}
            href="/dashboard/jobs"
          />
          <QuickActionCard
            title="Analytics"
            description="View insights"
            icon={<TrendingUp className="w-6 h-6" />}
            href="/dashboard/analytics"
          />
          <QuickActionCard
            title="Anomalies"
            description="Review flagged transactions"
            icon={<AlertCircle className="w-6 h-6" />}
            href="/dashboard/anomalies"
          />
        </div>

        {/* Info Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Getting Started</CardTitle>
              <CardDescription>Upload your first CSV file</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Upload a CSV file with transaction data to get AI-powered insights,
                anomaly detection, and beautiful visualizations.
              </p>
              <Link href="/dashboard/upload">
                <Button>Upload Now</Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Features</CardTitle>
              <CardDescription>What we analyze</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span>Data Cleaning & Normalization</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-500" />
                <span>Anomaly Detection</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-purple-500" />
                <span>AI Category Classification</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-yellow-500" />
                <span>Risk Assessment</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Need Help?</CardTitle>
              <CardDescription>Documentation & Support</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Check out our documentation to learn more about the platform
                and how to get the most out of your data.
              </p>
              <Button variant="outline">View Docs</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function QuickActionCard({
  title,
  description,
  icon,
  href,
}: {
  title: string
  description: string
  icon: React.ReactNode
  href: string
}) {
  return (
    <Link href={href}>
      <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
        <CardHeader>
          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-2 text-primary">
            {icon}
          </div>
          <CardTitle className="text-lg">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
      </Card>
    </Link>
  )
}
