import { useState, useEffect } from 'react'

type State<T> = { data: T | null; loading: boolean; error: string | null }

export function useApi<T>(url: string): State<T> {
  const [state, setState] = useState<State<T>>({ data: null, loading: true, error: null })

  useEffect(() => {
    let cancelled = false
    setState({ data: null, loading: true, error: null })
    fetch(url)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => { if (!cancelled) setState({ data, loading: false, error: null }) })
      .catch(e => { if (!cancelled) setState({ data: null, loading: false, error: String(e) }) })
    return () => { cancelled = true }
  }, [url])

  return state
}