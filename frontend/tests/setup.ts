import '@testing-library/jest-dom'

class MockWebSocket {
  url: string
  onopen: (() => void) | null = null
  onmessage: ((event: any) => void) | null = null
  onclose: (() => void) | null = null
  onerror: ((event: any) => void) | null = null
  readyState: number = 0
  
  constructor(url: string) {
    this.url = url
    setTimeout(() => {
      this.readyState = 1
      if (this.onopen) this.onopen()
    }, 0)
  }
  send(data: string) {}
  close() {
    this.readyState = 3
    if (this.onclose) this.onclose()
  }
}

global.WebSocket = MockWebSocket as any
