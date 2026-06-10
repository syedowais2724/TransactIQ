import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, Shield, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface RiskBadgeProps {
  level: 'low' | 'medium' | 'high'
  className?: string
  showIcon?: boolean
  animate?: boolean
}

export function RiskBadge({ level, className, showIcon = true, animate = true }: RiskBadgeProps) {
  const config = getRiskConfig(level)
  
  const BadgeContent = () => (
    <div className={cn(
      'inline-flex items-center gap-2 px-4 py-2 rounded-full font-semibold text-sm',
      'border-2 backdrop-blur-sm transition-all duration-300',
      config.className,
      className
    )}>
      {showIcon && <config.icon className="w-4 h-4" />}
      <span>Risk: {level.toUpperCase()}</span>
    </div>
  )
  
  if (!animate) {
    return <BadgeContent />
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.05 }}
      className="inline-block"
    >
      <div className="relative">
        {/* Glow effect */}
        <div className={cn(
          'absolute inset-0 rounded-full blur-md opacity-50',
          config.glowClass
        )} />
        
        {/* Badge */}
        <div className="relative">
          <BadgeContent />
        </div>
      </div>
    </motion.div>
  )
}

function getRiskConfig(level: 'low' | 'medium' | 'high') {
  switch (level) {
    case 'low':
      return {
        icon: Shield,
        className: 'text-green-600 bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-green-500/40 hover:border-green-500/60',
        glowClass: 'bg-green-500/30'
      }
    case 'medium':
      return {
        icon: AlertCircle,
        className: 'text-yellow-600 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border-yellow-500/40 hover:border-yellow-500/60',
        glowClass: 'bg-yellow-500/30'
      }
    case 'high':
      return {
        icon: AlertTriangle,
        className: 'text-red-600 bg-gradient-to-r from-red-500/20 to-rose-500/20 border-red-500/40 hover:border-red-500/60',
        glowClass: 'bg-red-500/30'
      }
  }
}
