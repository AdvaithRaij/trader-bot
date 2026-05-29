import React, { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { MarketTicker } from './MarketTicker'
import { CommandPalette } from './CommandPalette'
import { cn } from '../lib/utils'

export function Layout() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarWidth, setSidebarWidth] = useState(256) // 64 * 4 = 256px (w-64)
  const [isResizing, setIsResizing] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // Responsive sidebar handling
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      
      if (mobile) {
        setSidebarCollapsed(false)
        setSidebarOpen(false)
      } else if (window.innerWidth < 1024) {
        setSidebarCollapsed(true)
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Handle Command Palette keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen(true)
      }
      // Toggle sidebar with Cmd/Ctrl + B
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault()
        if (isMobile) {
          setSidebarOpen(!sidebarOpen)
        } else {
          setSidebarCollapsed(!sidebarCollapsed)
        }
      }
      // Close mobile sidebar on Escape
      if (e.key === 'Escape' && isMobile) {
        setSidebarOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [sidebarOpen, sidebarCollapsed])

  // Handle sidebar resizing
  const handleMouseDown = (e: React.MouseEvent) => {
    if (isMobile) return
    setIsResizing(true)
  }

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return
      e.preventDefault()
      const newWidth = Math.min(Math.max(e.clientX, 200), 400) // Min 200px, Max 400px
      setSidebarWidth(newWidth)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      // Prevent text selection during resize
      document.body.style.userSelect = 'none'
      document.body.style.pointerEvents = 'none'
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    } else {
      // Restore text selection
      document.body.style.userSelect = ''
      document.body.style.pointerEvents = ''
    }

    return () => {
      document.body.style.userSelect = ''
      document.body.style.pointerEvents = ''
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  const handleNavigate = (path: string) => {
    // This will be handled by React Router
    window.location.href = path
  }

  const handleExecuteAction = async (action: string) => {
    switch (action) {
      case 'start-bot':
        // TODO: Implement start bot API call
        console.log('Starting trading bot...')
        break
      case 'stop-bot':
        // TODO: Implement stop bot API call
        console.log('Stopping trading bot...')
        break
      case 'refresh-data':
        // TODO: Implement data refresh
        console.log('Refreshing market data...')
        break
      case 'run-screener':
        // TODO: Implement screener execution
        console.log('Running stock screener...')
        break
      default:
        console.log('Unknown action:', action)
    }
  }

  return (
    <div 
      className="min-h-screen bg-background text-foreground"
      style={{
        background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 25%, #16213e 50%, #0f0f23 100%)',
        backgroundAttachment: 'fixed',
        overscrollBehavior: 'none',
        WebkitOverscrollBehavior: 'none'
      }}
    >
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          "fixed top-0 left-0 h-full z-50 transition-all duration-300",
          // Desktop visibility
          "hidden md:block",
          // Mobile - show when open
          sidebarOpen && "block"
        )}
        style={{
          width: !isMobile && !sidebarCollapsed ? `${sidebarWidth}px` : 
                 !isMobile && sidebarCollapsed ? '64px' : 
                 sidebarOpen ? '256px' : '0px'
        }}
      >
        <Sidebar 
          collapsed={sidebarCollapsed}
          onToggle={() => {
            if (isMobile) {
              setSidebarOpen(!sidebarOpen)
            } else {
              setSidebarCollapsed(!sidebarCollapsed)
            }
          }}
          onClose={() => setSidebarOpen(false)}
          width={sidebarWidth}
        />
        
        {/* Resize Handle */}
        {!sidebarCollapsed && !isMobile && (
          <div
            className="absolute top-0 right-0 w-1 h-full cursor-col-resize bg-white/10 hover:bg-white/20 transition-colors group select-none"
            onMouseDown={handleMouseDown}
            style={{ pointerEvents: isResizing ? 'auto' : 'auto' }}
          >
            <div className="absolute top-1/2 right-0 transform -translate-y-1/2 w-3 h-12 bg-white/20 rounded-l opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
          </div>
        )}
      </div>

      {/* Main Content */}
      <div 
        className="main-content min-h-screen transition-all duration-300 overscroll-none"
        style={{
          marginLeft: !isMobile && !sidebarCollapsed ? `${sidebarWidth}px` : 
                     !isMobile && sidebarCollapsed ? '64px' : 
                     '0px',
          overscrollBehavior: 'none',
          WebkitOverscrollBehavior: 'none'
        }}
      >
        {/* Topbar */}
        <Topbar 
          onCommandPaletteOpen={() => setCommandPaletteOpen(true)}
          onSidebarToggle={() => {
            if (isMobile) {
              setSidebarOpen(!sidebarOpen)
            } else {
              setSidebarCollapsed(!sidebarCollapsed)
            }
          }}
          sidebarCollapsed={sidebarCollapsed}
          showMobileMenu={isMobile}
        />

        {/* Market Ticker */}
        <MarketTicker />

        {/* Page Content */}
        <main className="flex-1 p-3 sm:p-4 md:p-6 overflow-auto min-w-0 overscroll-none">
          <div className="max-w-7xl mx-auto min-w-0">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Command Palette */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onNavigate={handleNavigate}
        onExecuteAction={handleExecuteAction}
      />

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'rgba(15, 15, 35, 0.95)',
            color: 'white',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            backdropFilter: 'blur(12px)',
          },
          success: {
            style: {
              border: '1px solid rgba(34, 197, 94, 0.3)',
            },
          },
          error: {
            style: {
              border: '1px solid rgba(239, 68, 68, 0.3)',
            },
          },
        }}
      />
    </div>
  )
}
