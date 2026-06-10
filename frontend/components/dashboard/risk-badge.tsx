'use client'

import { AlertTriangle, ShieldAlert, ShieldCheck } from 'lucide-react'
import { motion } from 'framer-motion'
import { Badge } from '@/components/ui/badge'
import { cn, getRiskBadgeClass, type RiskLevel } from '@/lib/utils'

interface RiskBadgeProps {
  risk: RiskLevel
  className?: string
}

export function RiskBadge({ risk, className }: RiskBadgeProps) {
  const Icon = risk === 'low' ? ShieldCheck : risk === 'medium' ? AlertTriangle : ShieldAlert

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.25 }}
    >
      <Badge
        variant="outline"
        className={cn(
          'gap-1.5 px-3 py-1.5 text-xs uppercase tracking-wide backdrop-blur transition-transform hover:scale-[1.02]',
          getRiskBadgeClass(risk),
          className
        )}
      >
        <Icon className="h-3.5 w-3.5" />
        {risk} risk
      </Badge>
    </motion.div>
  )
}
