import { useEffect, useRef, useCallback, useState } from 'react'

const getWsBase = () => {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/ws`
}

export function useWebSocket(boardId: number, onEvent: (e: any) => void) {
  const ws = useRef<WebSocket | null>(null)
  const reconnect = useRef<ReturnType<typeof setTimeout>>()
  const ping = useRef<ReturnType<typeof setInterval>>()
  const [connected, setConnected] = useState(false)

  const connect = useCallback(() => {
    const token = localStorage.getItem('access_token')
    if (!token || !boardId) return

    ws.current = new WebSocket(`${getWsBase()}/${boardId}?token=${token}`)

    ws.current.onopen = () => {
      setConnected(true)
      ping.current = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN)
          ws.current.send(JSON.stringify({ type: 'ping' }))
      }, 25000)
    }

    ws.current.onmessage = (e) => {
      try { onEvent(JSON.parse(e.data)) } catch {}
    }

    ws.current.onclose = (e) => {
      setConnected(false)
      clearInterval(ping.current)
      if (e.code !== 1000 && e.code !== 4001 && e.code !== 4003)
        reconnect.current = setTimeout(connect, 3000)
    }

    ws.current.onerror = () => ws.current?.close()
  }, [boardId, onEvent])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnect.current)
      clearInterval(ping.current)
      ws.current?.close(1000)
    }
  }, [connect])

  const send = useCallback((data: object) => {
    if (ws.current?.readyState === WebSocket.OPEN)
      ws.current.send(JSON.stringify(data))
  }, [])

  return { connected, send }
}
