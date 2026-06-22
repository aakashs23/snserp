"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User as UserIcon, FileText, Loader2 } from "lucide-react"
import { createClient } from "@/utils/supabase/client"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"

interface Citation {
  document_id: string
  file_name: string
  snippet: string
}

interface Message {
  id: string
  role: "user" | "ai"
  content: string
  citations?: Citation[]
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "ai",
      content: "Hello! I'm your AI Assistant. I can answer questions based on the company documents you have uploaded. How can I help you today?"
    }
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = { id: Date.now().toString(), role: "user", content: input }
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setLoading(true)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      const res = await fetch(`${API_URL}/api/v1/chat/query`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session?.access_token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userMessage.content })
      })

      if (res.ok) {
        const data = await res.json()
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "ai",
          content: data.answer,
          citations: data.citations
        }
        setMessages(prev => [...prev, aiMessage])
      } else {
        toast.error("Failed to get response from AI")
      }
    } catch {
      toast.error("Network error while connecting to AI")
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = async (document_id: string) => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      
      const res = await fetch(`${API_URL}/api/v1/documents/${document_id}/preview`, {
        headers: { "Authorization": `Bearer ${session?.access_token}` }
      })
      if (res.ok) {
        const data = await res.json()
        window.open(data.url, "_blank")
      } else {
        toast.error("Could not generate preview link")
      }
    } catch {
      toast.error("Network error")
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
          AI Assistant
        </h1>
        <p className="text-muted-foreground mt-1">
          Ask questions about your business data and uploaded documents.
        </p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'ai' && (
                  <div className="flex-shrink-0 size-8 rounded-full bg-chart-4 flex items-center justify-center text-white">
                    <Bot className="size-5" />
                  </div>
                )}
                
                <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`p-4 rounded-2xl ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                  </div>
                  
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="flex flex-col gap-2 mt-2 w-full">
                      <p className="text-xs text-muted-foreground font-medium">Sources:</p>
                      <div className="flex flex-wrap gap-2">
                        {msg.citations.map((cite, i) => (
                          <button
                            key={i}
                            onClick={() => handlePreview(cite.document_id)}
                            className="flex items-center gap-1.5 text-xs bg-background border rounded-md px-2.5 py-1.5 hover:bg-accent hover:text-white transition-colors"
                            title={cite.snippet}
                          >
                            <FileText className="size-3" />
                            <span className="truncate max-w-[150px]">{cite.file_name}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="flex-shrink-0 size-8 rounded-full bg-accent flex items-center justify-center text-white">
                    <UserIcon className="size-5" />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-4 justify-start">
                <div className="flex-shrink-0 size-8 rounded-full bg-chart-4 flex items-center justify-center text-white">
                  <Bot className="size-5" />
                </div>
                <div className="p-4 rounded-2xl bg-muted flex items-center gap-2">
                  <Loader2 className="size-4 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        <div className="p-4 border-t bg-background">
          <div className="max-w-3xl mx-auto relative">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask me anything..."
              className="pr-12 py-6 rounded-full bg-muted/50 focus-visible:ring-1"
              disabled={loading}
            />
            <Button 
              size="icon" 
              className="absolute right-1.5 top-1.5 h-9 w-9 rounded-full" 
              onClick={handleSend}
              disabled={!input.trim() || loading}
            >
              <Send className="size-4 ml-0.5" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
