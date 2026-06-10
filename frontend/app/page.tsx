'use client'

import { motion } from 'framer-motion'
import { ArrowRight, Upload, TrendingUp, Shield, Zap } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-secondary/20">
      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-20 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center max-w-4xl mx-auto"
        >
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8"
          >
            <Zap className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">AI-Powered Transaction Analytics</span>
          </motion.div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-white/60">
            Transform Your Transaction Data into Insights
          </h1>

          <p className="text-xl text-muted-foreground mb-12 max-w-2xl mx-auto">
            Upload CSV files and get AI-powered analysis with anomaly detection,
            smart categorization, and actionable insights in seconds.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/dashboard/upload">
              <Button size="lg" className="gap-2 group">
                Get Started
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline" className="gap-2">
                View Dashboard
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <FeatureCard
            icon={<Upload className="w-8 h-8" />}
            title="Instant Upload"
            description="Drag and drop CSV files for instant processing with real-time progress tracking"
            delay={0.1}
          />
          <FeatureCard
            icon={<Shield className="w-8 h-8" />}
            title="Anomaly Detection"
            description="AI automatically identifies suspicious transactions and unusual patterns"
            delay={0.2}
          />
          <FeatureCard
            icon={<TrendingUp className="w-8 h-8" />}
            title="Smart Analytics"
            description="Beautiful charts and insights powered by advanced AI algorithms"
            delay={0.3}
          />
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">How It Works</h2>
          <div className="space-y-8">
            <Step
              number="1"
              title="Upload Your CSV"
              description="Simply drag and drop your transaction CSV file"
              delay={0.1}
            />
            <Step
              number="2"
              title="AI Processing"
              description="Our AI cleans, categorizes, and analyzes your data"
              delay={0.2}
            />
            <Step
              number="3"
              title="Get Insights"
              description="View beautiful dashboards with actionable insights"
              delay={0.3}
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto text-center p-12 rounded-2xl glass border"
        >
          <h2 className="text-3xl font-bold mb-4">
            Ready to Transform Your Transaction Data?
          </h2>
          <p className="text-muted-foreground mb-8">
            Start analyzing your transactions with AI-powered insights today.
          </p>
          <Link href="/dashboard/upload">
            <Button size="lg" className="gap-2">
              Start Free Upload
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </motion.div>
      </section>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
  delay,
}: {
  icon: React.ReactNode
  title: string
  description: string
  delay: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay }}
      className="p-6 rounded-xl glass border hover:border-primary/50 transition-colors"
    >
      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4 text-primary">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </motion.div>
  )
}

function Step({
  number,
  title,
  description,
  delay,
}: {
  number: string
  title: string
  description: string
  delay: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ delay }}
      className="flex gap-6 items-start"
    >
      <div className="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-xl flex-shrink-0">
        {number}
      </div>
      <div>
        <h3 className="text-2xl font-semibold mb-2">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </motion.div>
  )
}
