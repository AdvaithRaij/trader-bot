import React, { useState, useEffect, useCallback } from 'react'
import {
  Play,
  Pause,
  RefreshCw,
  Search,
  Brain,
  Zap,
  Activity,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  Clock,
  BarChart3,
  Target,
  Shield
} from 'lucide-react'
import { cn } from '../lib/utils'
import { 
  apiService, 
  pipelineWebSocket,
  type PipelineStatus,
  type PipelineState,
  type PipelineMetrics,
  type ScreenerCandidate,
  type TradePlan,
  type ExecutorPosition,
  type PipelineEvent
} from '../lib/trading-api'

interface PipelineDashboardProps {
  onCandidateSelect?: (symbol: string) => void
}

const PIPELINE_STAGES = [
  { key: 'SCREENING', label: 'Stock Screener', icon: Search, color: 'blue' },
  { key: 'ANALYZING', label: 'AI Analysis', icon: Brain, color: 'purple' },
  { key: 'EXECUTING', label: 'Trade Executor', icon: Zap, color: 'green' }
]

const STATE_LABELS: Record<PipelineState, string> = {
  IDLE: 'Idle',
  SCREENING: 'Screening Stocks',
  ANALYZING: 'AI Analyzing',
  EXECUTING: 'Executing Trades',
  MONITORING: 'Monitoring Positions',
  SQUARING_OFF: 'Squaring Off',
  STOPPED: 'Stopped'
}

const STATE_COLORS: Record<PipelineState, string> = {
  IDLE: 'text-gray-400',
  SCREENING: 'text-blue-400',
  ANALYZING: 'text-purple-400',
  EXECUTING: 'text-green-400',
  MONITORING: 'text-cyan-400',
  SQUARING_OFF: 'text-orange-400',
  STOPPED: 'text-red-400'
}

export function PipelineDashboard({ onCandidateSelect }: PipelineDashboardProps) {
  const [status, setStatus] = useState<PipelineStatus | null>(null)
  const [candidates, setCandidates] = useState<ScreenerCandidate[]>([])
  const [tradePlans, setTradePlans] = useState<TradePlan[]>([])
  const [positions, setPositions] = useState<ExecutorPosition[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [wsConnected, setWsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadPipelineData = useCallback(async () => {
    try {
      setError(null)
      const [statusData, screenerData, plansData] = await Promise.all([
        apiService.getPipelineStatus().catch(() => null),
        apiService.getScreenerResults().catch(() => null),
        apiService.getTradePlans().catch(() => null)
      ])

      if (statusData) setStatus(statusData)
      if (screenerData) setCandidates(screenerData.candidates || [])
      if (plansData) setTradePlans(plansData.plans || [])
    } catch (err) {
      console.error('Error loading pipeline data:', err)
      setError('Failed to load pipeline data')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handlePipelineEvent = useCallback((event: PipelineEvent) => {
    switch (event.type) {
      case 'state_change':
        setStatus(prev => prev ? { ...prev, state: event.data.state } : null)
        break
      case 'screening_complete':
        setCandidates(event.data.candidates || [])
        break
      case 'analysis_complete':
        setTradePlans(prev => [...prev, event.data.plan])
        break
      case 'trade_executed':
        loadPipelineData()
        break
      case 'position_update':
        setPositions(event.data.positions || [])
        break
      case 'metrics_update':
        setStatus(prev => prev ? { ...prev, metrics: event.data } : null)
        break
    }
  }, [loadPipelineData])

  useEffect(() => {
    loadPipelineData()
    
    pipelineWebSocket.connect(
      handlePipelineEvent,
      (connected) => setWsConnected(connected)
    )

    const interval = setInterval(loadPipelineData, 30000)
    
    return () => {
      clearInterval(interval)
      pipelineWebSocket.disconnect()
    }
  }, [loadPipelineData, handlePipelineEvent])

  const handleStartPipeline = async () => {
    try {
      await apiService.startPipeline()
      loadPipelineData()
    } catch (err) {
      console.error('Failed to start pipeline:', err)
    }
  }

  const handleStopPipeline = async () => {
    try {
      await apiService.stopPipeline()
      loadPipelineData()
    } catch (err) {
      console.error('Failed to stop pipeline:', err)
    }
  }

  const handleTriggerScreening = async () => {
    try {
      await apiService.triggerScreening()
    } catch (err) {
      console.error('Failed to trigger screening:', err)
    }
  }

  const getActiveStageIndex = (): number => {
    if (!status) return -1
    switch (status.state) {
      case 'SCREENING': return 0
      case 'ANALYZING': return 1
      case 'EXECUTING': return 2
      case 'MONITORING': return 2
      default: return -1
    }
  }

  const formatTime = (isoString: string | null) => {
    if (!isoString) return '--:--'
    return new Date(isoString).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const activeStageIndex = getActiveStageIndex()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Pipeline Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-bold text-white">Trading Pipeline</h2>
          <div className={cn(
            "flex items-center gap-2 px-3 py-1 rounded-full text-sm",
            status?.is_running ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
          )}>
            <div className={cn(
              "w-2 h-2 rounded-full",
              status?.is_running ? 'bg-green-400 animate-pulse' : 'bg-gray-500'
            )} />
            {status ? STATE_LABELS[status.state] : 'Disconnected'}
          </div>
          {wsConnected && (
            <div className="flex items-center gap-1 text-xs text-green-400">
              <Activity className="w-3 h-3" />
              Live
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleTriggerScreening}
            disabled={!status?.is_running}
            className="flex items-center gap-2 px-3 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50"
          >
            <Search className="w-4 h-4" />
            Screen Now
          </button>
          {status?.is_running ? (
            <button
              onClick={handleStopPipeline}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
            >
              <Pause className="w-4 h-4" />
              Stop
            </button>
          ) : (
            <button
              onClick={handleStartPipeline}
              className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
            >
              <Play className="w-4 h-4" />
              Start
            </button>
          )}
        </div>
      </div>

      {/* 3-Stage Pipeline Visualization */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          {PIPELINE_STAGES.map((stage, index) => (
            <React.Fragment key={stage.key}>
              <div className={cn(
                "flex flex-col items-center gap-3 flex-1",
                activeStageIndex === index && "scale-105"
              )}>
                <div className={cn(
                  "w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300",
                  activeStageIndex === index
                    ? `bg-${stage.color}-500/30 ring-2 ring-${stage.color}-400`
                    : activeStageIndex > index
                      ? 'bg-green-500/20'
                      : 'bg-gray-700/50'
                )}>
                  {activeStageIndex > index ? (
                    <CheckCircle className="w-8 h-8 text-green-400" />
                  ) : (
                    <stage.icon className={cn(
                      "w-8 h-8",
                      activeStageIndex === index
                        ? `text-${stage.color}-400 animate-pulse`
                        : 'text-gray-500'
                    )} />
                  )}
                </div>
                <div className="text-center">
                  <p className={cn(
                    "font-medium",
                    activeStageIndex === index ? 'text-white' : 'text-gray-400'
                  )}>
                    {stage.label}
                  </p>
                  <p className="text-xs text-gray-500">
                    {stage.key === 'SCREENING' && `${candidates.length} candidates`}
                    {stage.key === 'ANALYZING' && `${tradePlans.length} plans`}
                    {stage.key === 'EXECUTING' && `${status?.metrics?.open_positions || 0} positions`}
                  </p>
                </div>
              </div>
              {index < PIPELINE_STAGES.length - 1 && (
                <div className={cn(
                  "flex-1 h-1 mx-4 rounded-full transition-colors",
                  activeStageIndex > index ? 'bg-green-500' : 'bg-gray-700'
                )} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <MetricCard
          icon={<BarChart3 className="w-5 h-5 text-blue-400" />}
          label="Screenings"
          value={status?.metrics?.total_screenings || 0}
        />
        <MetricCard
          icon={<Brain className="w-5 h-5 text-purple-400" />}
          label="Analyses"
          value={status?.metrics?.total_analyses || 0}
        />
        <MetricCard
          icon={<Zap className="w-5 h-5 text-green-400" />}
          label="Trades Today"
          value={`${status?.metrics?.trades_today || 0}/10`}
        />
        <MetricCard
          icon={<Target className="w-5 h-5 text-cyan-400" />}
          label="Win Rate"
          value={status?.metrics?.successful_trades && status?.metrics?.total_executions
            ? `${((status.metrics.successful_trades / status.metrics.total_executions) * 100).toFixed(0)}%`
            : '0%'}
        />
        <MetricCard
          icon={<Shield className="w-5 h-5 text-yellow-400" />}
          label="Open Risk"
          value={`${(status?.metrics?.open_risk_percent || 0).toFixed(1)}%`}
          alert={!!(status?.metrics?.open_risk_percent && status.metrics.open_risk_percent > 4)}
        />
        <MetricCard
          icon={status?.metrics?.total_pnl && status.metrics.total_pnl >= 0
            ? <TrendingUp className="w-5 h-5 text-green-400" />
            : <TrendingDown className="w-5 h-5 text-red-400" />}
          label="Today P&L"
          value={`₹${(status?.metrics?.total_pnl || 0).toLocaleString()}`}
          positive={!!(status?.metrics?.total_pnl && status.metrics.total_pnl >= 0)}
        />
      </div>

      {/* Timing Info */}
      <div className="flex items-center justify-between text-sm text-gray-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            Last Screen: {formatTime(status?.last_screening_time || null)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            Next Screen: {formatTime(status?.next_screening_time || null)}
          </span>
        </div>
        <span>Cycle #{status?.current_cycle || 0}</span>
      </div>
    </div>
  )
}

// Metric Card Component
interface MetricCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  positive?: boolean
  alert?: boolean
}

function MetricCard({ icon, label, value, positive, alert }: MetricCardProps) {
  return (
    <div className={cn(
      "glass-card p-4 flex flex-col gap-2",
      alert && "ring-1 ring-red-500/50"
    )}>
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-xs text-gray-400">{label}</span>
      </div>
      <span className={cn(
        "text-xl font-bold",
        positive === true && "text-green-400",
        positive === false && "text-red-400",
        positive === undefined && "text-white",
        alert && "text-red-400"
      )}>
        {value}
      </span>
    </div>
  )
}

