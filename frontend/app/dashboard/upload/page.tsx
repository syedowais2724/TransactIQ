'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, CheckCircle, Loader2, AlertCircle, Sparkles } from 'lucide-react'
import { uploadCSV } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

type ProcessingStage = {
  id: string
  label: string
  status: 'pending' | 'active' | 'completed' | 'error'
}

export default function UploadPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [stages, setStages] = useState<ProcessingStage[]>([
    { id: 'upload', label: 'Uploading CSV', status: 'pending' },
    { id: 'clean', label: 'Cleaning Data', status: 'pending' },
    { id: 'anomaly', label: 'Detecting Anomalies', status: 'pending' },
    { id: 'classify', label: 'AI Classification', status: 'pending' },
    { id: 'summary', label: 'Generating Summary', status: 'pending' },
    { id: 'finalize', label: 'Finalizing Results', status: 'pending' },
  ])

  const updateStage = (stageId: string, status: ProcessingStage['status']) => {
    setStages(prev => prev.map(s => s.id === stageId ? { ...s, status } : s))
  }

  const simulateProcessing = async (jobId: number) => {
    // Simulate processing stages
    const stageTiming = [
      { id: 'upload', duration: 500 },
      { id: 'clean', duration: 1000 },
      { id: 'anomaly', duration: 1000 },
      { id: 'classify', duration: 2000 },
      { id: 'summary', duration: 1000 },
      { id: 'finalize', duration: 500 },
    ]

    let cumulativeProgress = 0
    const progressPerStage = 100 / stageTiming.length

    for (const stage of stageTiming) {
      updateStage(stage.id, 'active')
      
      await new Promise(resolve => setTimeout(resolve, stage.duration))
      
      updateStage(stage.id, 'completed')
      cumulativeProgress += progressPerStage
      setProgress(cumulativeProgress)
    }

    // Auto-redirect to results
    setTimeout(() => {
      router.push(`/dashboard/results/${jobId}`)
    }, 800)
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)
    setProgress(0)

    try {
      updateStage('upload', 'active')
      const response = await uploadCSV(file)
      updateStage('upload', 'completed')
      
      // Start simulated processing animation
      await simulateProcessing(response.job_id)
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
      stages.forEach(stage => {
        if (stage.status === 'active') {
          updateStage(stage.id, 'error')
        }
      })
      setUploading(false)
    }
  }

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const csvFile = acceptedFiles[0]
      if (csvFile.name.endsWith('.csv')) {
        setFile(csvFile)
        setError(null)
      } else {
        setError('Please upload a CSV file')
      }
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: false,
    disabled: uploading
  })

  if (uploading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-2xl"
        >
          <Card className="border-2">
            <CardContent className="p-8">
              {/* Header */}
              <div className="text-center mb-8">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  className="inline-block mb-4"
                >
                  <Sparkles className="w-12 h-12 text-primary" />
                </motion.div>
                <h2 className="text-2xl font-bold mb-2">Processing Your Data</h2>
                <p className="text-muted-foreground">
                  AI-powered analysis in progress...
                </p>
              </div>

              {/* Progress Bar */}
              <div className="mb-8">
                <Progress value={progress} className="h-2 mb-2" />
                <p className="text-sm text-muted-foreground text-center">
                  {Math.round(progress)}% complete
                </p>
              </div>

              {/* Processing Stages */}
              <div className="space-y-3">
                {stages.map((stage, index) => (
                  <motion.div
                    key={stage.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                      stage.status === 'completed'
                        ? 'bg-green-500/10'
                        : stage.status === 'active'
                        ? 'bg-blue-500/10'
                        : stage.status === 'error'
                        ? 'bg-red-500/10'
                        : 'bg-muted/50'
                    }`}
                  >
                    {/* Icon */}
                    <div className="flex-shrink-0">
                      {stage.status === 'completed' && (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      )}
                      {stage.status === 'active' && (
                        <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                      )}
                      {stage.status === 'error' && (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      )}
                      {stage.status === 'pending' && (
                        <div className="w-5 h-5 rounded-full border-2 border-muted" />
                      )}
                    </div>

                    {/* Label */}
                    <span className={`font-medium ${
                      stage.status === 'completed'
                        ? 'text-green-600'
                        : stage.status === 'active'
                        ? 'text-blue-600'
                        : stage.status === 'error'
                        ? 'text-red-600'
                        : 'text-muted-foreground'
                    }`}>
                      {stage.label}
                    </span>

                    {/* Status Text */}
                    {stage.status === 'active' && (
                      <span className="ml-auto text-sm text-blue-500">
                        Processing...
                      </span>
                    )}
                    {stage.status === 'completed' && (
                      <span className="ml-auto text-sm text-green-500">
                        Done
                      </span>
                    )}
                  </motion.div>
                ))}
              </div>

              {/* Redirecting Message */}
              {progress === 100 && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 text-center text-sm text-muted-foreground"
                >
                  Redirecting to results dashboard...
                </motion.div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold mb-3">Upload Transaction Data</h1>
          <p className="text-lg text-muted-foreground">
            Upload your CSV file for AI-powered analysis
          </p>
        </motion.div>

        {/* Upload Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-2">
            <CardContent className="p-8">
              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={`relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-300 ${
                  isDragActive
                    ? 'border-primary bg-primary/5 scale-[1.02]'
                    : file
                    ? 'border-green-500 bg-green-500/5'
                    : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-primary/5'
                }`}
              >
                <input {...getInputProps()} />

                {/* Animated Glow Effect */}
                <AnimatePresence>
                  {isDragActive && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="absolute inset-0 rounded-lg bg-primary/10 backdrop-blur-sm"
                    />
                  )}
                </AnimatePresence>

                <div className="relative z-10">
                  {/* Icon */}
                  <motion.div
                    animate={isDragActive ? { scale: 1.1, rotate: 5 } : { scale: 1, rotate: 0 }}
                    className="inline-block mb-4"
                  >
                    {file ? (
                      <FileText className="w-16 h-16 text-green-500 mx-auto" />
                    ) : (
                      <Upload className="w-16 h-16 text-muted-foreground mx-auto" />
                    )}
                  </motion.div>

                  {/* Text */}
                  {file ? (
                    <div>
                      <p className="text-xl font-semibold text-green-600 mb-2">
                        {file.name}
                      </p>
                      <p className="text-sm text-muted-foreground mb-4">
                        {(file.size / 1024).toFixed(2)} KB • Ready to upload
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-xl font-semibold mb-2">
                        {isDragActive ? 'Drop your CSV here' : 'Drag & drop your CSV file'}
                      </p>
                      <p className="text-sm text-muted-foreground mb-4">
                        or click to browse
                      </p>
                    </div>
                  )}

                  {/* Requirements */}
                  <div className="text-xs text-muted-foreground">
                    <p>Supported format: CSV</p>
                    <p>Max file size: 10MB</p>
                  </div>
                </div>
              </div>

              {/* Error Message */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg"
                  >
                    <div className="flex items-center gap-2 text-red-600">
                      <AlertCircle className="w-5 h-5" />
                      <span className="font-medium">{error}</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Upload Button */}
              {file && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6"
                >
                  <Button
                    onClick={handleUpload}
                    disabled={uploading}
                    className="w-full h-12 text-lg font-semibold"
                    size="lg"
                  >
                    {uploading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5 mr-2" />
                        Start AI Analysis
                      </>
                    )}
                  </Button>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Info Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid md:grid-cols-3 gap-4 mt-8"
        >
          {[
            { icon: '🧹', title: 'Data Cleaning', desc: 'Automatic normalization' },
            { icon: '🔍', title: 'Anomaly Detection', desc: 'Smart pattern recognition' },
            { icon: '🤖', title: 'AI Classification', desc: 'Gemini-powered insights' },
          ].map((feature, i) => (
            <Card key={i} className="text-center p-6 hover:shadow-lg transition-shadow">
              <div className="text-4xl mb-2">{feature.icon}</div>
              <h3 className="font-semibold mb-1">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.desc}</p>
            </Card>
          ))}
        </motion.div>
      </div>
    </div>
  )
}
