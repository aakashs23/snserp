"use client"

import React, { createContext, useContext, useState, useCallback } from "react"
import { createClient } from "@/utils/supabase/client"
import { toast } from "sonner"

export interface Citation {
  document_id: string
  file_name: string
  snippet: string
  page_number?: number | null
  chunk_index?: number | null
  relevance_score?: number | null
}

export interface ChatMessage {
  id: string
  role: "user" | "ai"
  content: string
  citations?: Citation[]
}

interface ChatContextType {
  isOpen: boolean
  toggleChat: () => void
  closeChat: () => void
  messages: ChatMessage[]
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
  sessionId: string | null
  setSessionId: React.Dispatch<React.SetStateAction<string | null>>
  isLoading: boolean
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>
  sendMessage: (content: string) => Promise<void>
  loadHistory: (id: string) => Promise<void>
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const toggleChat = () => setIsOpen(prev => !prev)
  const closeChat = () => setIsOpen(false)

  // Load history if a session is set
  const loadHistory = useCallback(async (id: string) => {
    setIsLoading(true)
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      
      const res = await fetch(`${API_URL}/api/v1/chat/sessions/${id}/messages`, {
        headers: { "Authorization": `Bearer ${session?.access_token}` }
      })
      if (res.ok) {
        const data = await res.json()
        const mapped: ChatMessage[] = data.map((msg: { id: string; role: string; message: string }) => ({
          id: msg.id,
          role: msg.role as "user" | "ai",
          content: msg.message,
          citations: [] // we'd need to parse them from the message if we stored them, or just rely on raw text
        }))
        setMessages(mapped)
        setSessionId(id)
      }
    } catch {
      toast.error("Failed to load chat history")
    } finally {
      setIsLoading(false)
    }
  }, [])

  const sendMessage = async (content: string) => {
    const userMsg: ChatMessage = { id: Date.now().toString(), role: "user", content }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      const res = await fetch(`${API_URL}/api/v1/chat/query`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session?.access_token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: content, session_id: sessionId })
      })

      if (res.ok) {
        const data = await res.json()
        if (!sessionId && data.session_id) {
          setSessionId(data.session_id)
        }
        
        const aiMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: "ai",
          content: data.answer,
          citations: data.citations
        }
        setMessages(prev => [...prev, aiMsg])
      } else {
        toast.error("Failed to get response")
        setMessages(prev => prev.filter(m => m.id !== userMsg.id)) // rollback on fail
      }
    } catch {
      toast.error("Network error")
      setMessages(prev => prev.filter(m => m.id !== userMsg.id)) // rollback on fail
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <ChatContext.Provider value={{
      isOpen, toggleChat, closeChat, messages, setMessages, 
      sessionId, setSessionId, isLoading, setIsLoading, sendMessage, loadHistory
    }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const context = useContext(ChatContext)
  if (!context) throw new Error("useChat must be used within ChatProvider")
  return context
}
