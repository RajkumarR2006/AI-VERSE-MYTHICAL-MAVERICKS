"use client"

import type React from "react"
import { useState } from "react"
import { AnimatePresence } from "framer-motion"
import { GradientBackground } from "./gradient-background"
import { ChatHeader } from "./chat-header"
import { ChatMessages } from "./chat-messages"
import { ChatInput } from "./chat-input"
import { SourcesSidebar } from "./sources-sidebar"
import { CursorGradient } from "./cursor-gradient"

export interface Source {
  source: string
  content: string
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: Source[]
  timestamp: Date
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [activeSources, setActiveSources] = useState<Source[]>([])
  const [showSources, setShowSources] = useState(false)

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const res = await fetch(" write your cloud flare link here/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input }),
      })

      const data = await res.json()

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
      setActiveSources(data.sources || [])
      if (data.sources?.length > 0) setShowSources(true)
    } catch {
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Unable to connect to the server. Please ensure your backend is running at http://127.0.0.1:8000",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0a0f1a]">
      {/* Animated gradient background */}
      <GradientBackground />

      <CursorGradient />

      {/* Main content */}
      <div className="relative z-10 flex h-screen">
        {/* Main chat area */}
        <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
          <ChatHeader />

          <ChatMessages messages={messages} isLoading={isLoading} onSuggestionClick={handleSuggestionClick} />

          <ChatInput value={input} onChange={setInput} onSubmit={handleSubmit} isLoading={isLoading} />
        </div>

        {/* Sources sidebar */}
        <AnimatePresence>
          {showSources && activeSources.length > 0 && (
            <SourcesSidebar sources={activeSources} onClose={() => setShowSources(false)} />
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
