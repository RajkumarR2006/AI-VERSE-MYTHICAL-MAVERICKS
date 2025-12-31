"use client"
import ReactMarkdown from "react-markdown"
import { useRef, useEffect, useState } from "react"
import type React from "react"

import { motion, AnimatePresence } from "framer-motion"
import { Copy, Check, Brain, Zap, UserCircle2 } from "lucide-react"
import type { Message } from "./chat-interface"

interface ChatMessagesProps {
  messages: Message[]
  isLoading: boolean
  onSuggestionClick?: (suggestion: string) => void
}

export function ChatMessages({ messages, isLoading, onSuggestionClick }: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
      {messages.length === 0 ? (
        <EmptyState onSuggestionClick={onSuggestionClick} />
      ) : (
        <div className="space-y-6 max-w-3xl mx-auto">
          <AnimatePresence mode="popLayout">
            {messages.map((message, index) => (
              <MessageBubble key={message.id} message={message} index={index} />
            ))}
          </AnimatePresence>

          {isLoading && <ThinkingIndicator />}
        </div>
      )}
    </div>
  )
}

function EmptyState({ onSuggestionClick }: { onSuggestionClick?: (suggestion: string) => void }) {
  const suggestions = [
    "What government schemes are available for startups?",
    "Explain MSME funding options",
    "How to apply for Startup India benefits?",
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="flex flex-col items-center justify-center h-full text-center px-4"
    >
      <motion.div
        className="relative mb-8"
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 4, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
      >
        <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-[#4f46e5] via-[#7c3aed] to-[#f43f5e] p-[3px]">
          <div className="w-full h-full rounded-3xl bg-[#0a0f1a] flex items-center justify-center relative overflow-hidden">
            {/* Inner gradient shimmer */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
              animate={{ x: ["-100%", "100%"] }}
              transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
            />
            <Brain className="w-12 h-12 text-white relative z-10" />
            {/* Animated sparkles */}
            <motion.div
              className="absolute top-2 right-2"
              animate={{ opacity: [0.4, 1, 0.4], rotate: [0, 15, 0] }}
              transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
            >
              <Zap className="w-4 h-4 text-[#60a5fa]" />
            </motion.div>
            <motion.div
              className="absolute bottom-2 left-2"
              animate={{ opacity: [0.6, 1, 0.6], rotate: [0, -15, 0] }}
              transition={{ duration: 2.5, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut", delay: 0.5 }}
            >
              <Zap className="w-3 h-3 text-[#f43f5e]" />
            </motion.div>
          </div>
        </div>
        {/* Glow */}
        <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-[#4f46e5] to-[#f43f5e] opacity-50 blur-2xl" />
      </motion.div>

      <h2 className="text-2xl font-semibold text-white mb-2">How can I help you today?</h2>
      <p className="text-slate-400 mb-8 max-w-md">
        Ask me anything about government schemes, funding options, and startup policies.
      </p>

      {/* Suggestions */}
      <div className="flex flex-col gap-3 w-full max-w-md">
        {suggestions.map((suggestion, i) => (
          <motion.button
            key={suggestion}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.1 }}
            whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.08)" }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onSuggestionClick?.(suggestion)}
            className="text-left px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-slate-300 hover:text-white hover:border-white/20 transition-all"
          >
            {suggestion}
          </motion.button>
        ))}
      </div>
    </motion.div>
  )
}

function MessageBubble({ message, index }: { message: Message; index: number }) {
  const isUser = message.role === "user"
  const [copied, setCopied] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setMousePos({
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100,
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className={`flex gap-4 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {isUser ? (
        <motion.div
          whileHover={{ scale: 1.1 }}
          className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-[#4f46e5] via-[#6366f1] to-[#818cf8] p-[2px] shadow-lg shadow-[#4f46e5]/30"
        >
          <div className="w-full h-full rounded-xl bg-[#0f172a] flex items-center justify-center">
            <UserCircle2 className="w-5 h-5 text-white" />
          </div>
        </motion.div>
      ) : (
        <motion.div whileHover={{ scale: 1.1 }} className="flex-shrink-0 relative">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#f43f5e] via-[#ec4899] to-[#d946ef] p-[2px] shadow-lg shadow-[#f43f5e]/30">
            <div className="w-full h-full rounded-xl bg-[#0f172a] flex items-center justify-center relative overflow-hidden">
              <Brain className="w-5 h-5 text-white relative z-10" />
              <motion.div
                className="absolute top-0.5 right-0.5"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY }}
              >
                <Zap className="w-2 h-2 text-[#60a5fa]" />
              </motion.div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Message */}
      <div className={`flex-1 max-w-2xl ${isUser ? "text-right" : ""}`}>
        {!isUser ? (
          <motion.div
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className="relative inline-block"
            whileHover={{ scale: 1.01 }}
          >
            <motion.div
              className="absolute -inset-[1px] rounded-2xl"
              style={{
                background: "linear-gradient(90deg, #4f46e5, #f43f5e, #60a5fa, #4f46e5)",
                backgroundSize: "300% 100%",
                opacity: 0.4,
              }}
              animate={{
                backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
              }}
              transition={{ duration: 6, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
            />

            <motion.div
              className="absolute -inset-2 rounded-2xl blur-lg pointer-events-none"
              style={{
                background: "linear-gradient(90deg, #4f46e5, #f43f5e, #60a5fa, #4f46e5)",
                backgroundSize: "300% 100%",
              }}
              animate={{
                backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
                opacity: isHovered ? 0.2 : 0.08,
              }}
              transition={{
                backgroundPosition: { duration: 6, repeat: Number.POSITIVE_INFINITY, ease: "linear" },
                opacity: { duration: 0.3, ease: "easeOut" },
              }}
            />

            {/* Inner content - NOW WITH REACT MARKDOWN */}
            <div className="relative px-5 py-4 rounded-2xl bg-[#0a0f1a] backdrop-blur-sm">
              <div className="text-sm leading-relaxed text-slate-200 relative z-10">
                <ReactMarkdown
                  components={{
                    p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                    strong: ({ node, ...props }) => <span className="font-bold text-white" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
                    ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
                    li: ({ node, ...props }) => <li className="marker:text-pink-500" {...props} />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            onMouseMove={handleMouseMove}
            className="relative inline-block"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {/* Cursor-following glow for user messages */}
            <motion.div
              className="absolute -inset-3 rounded-2xl blur-xl pointer-events-none"
              style={{
                background: `radial-gradient(circle at ${mousePos.x}% ${mousePos.y}%, rgba(79, 70, 229, 0.5) 0%, transparent 60%)`,
              }}
              animate={{ opacity: isHovered ? 0.8 : 0 }}
              transition={{ duration: 0.2 }}
            />

            {/* Outer shimmer ring on hover */}
            <motion.div
              className="absolute -inset-[2px] rounded-2xl"
              style={{
                background: "linear-gradient(135deg, #4f46e5, #818cf8, #6366f1, #4f46e5)",
                backgroundSize: "200% 200%",
              }}
              animate={{
                opacity: isHovered ? 1 : 0,
                backgroundPosition: ["0% 0%", "100% 100%", "0% 0%"],
              }}
              transition={{
                opacity: { duration: 0.2 },
                backgroundPosition: { duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "linear" },
              }}
            />

            {/* Main bubble */}
            <div className="relative px-5 py-3 rounded-2xl bg-gradient-to-r from-[#4f46e5] to-[#6366f1] overflow-hidden">
              {/* Interactive sparkle particles on hover */}
              <AnimatePresence>
                {isHovered && (
                  <>
                    {[...Array(5)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="absolute w-1 h-1 rounded-full bg-white"
                        initial={{
                          x: mousePos.x + "%",
                          y: mousePos.y + "%",
                          opacity: 0,
                          scale: 0,
                        }}
                        animate={{
                          x: `${mousePos.x + (Math.random() - 0.5) * 40}%`,
                          y: `${mousePos.y + (Math.random() - 0.5) * 40}%`,
                          opacity: [0, 1, 0],
                          scale: [0, 1.5, 0],
                        }}
                        transition={{
                          duration: 0.8,
                          delay: i * 0.05,
                          ease: "easeOut",
                        }}
                      />
                    ))}
                  </>
                )}
              </AnimatePresence>

              {/* Shimmer sweep */}
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none"
                initial={{ x: "-100%" }}
                animate={{ x: isHovered ? "200%" : "-100%" }}
                transition={{ duration: 0.6, ease: "easeInOut" }}
              />

              <p className="text-sm leading-relaxed whitespace-pre-wrap text-white relative z-10 font-medium">
                {message.content}
              </p>
            </div>
          </motion.div>
        )}

        {/* Actions */}
        {!isUser && (
          <motion.div
            className="flex items-center gap-2 mt-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <span className="text-xs text-slate-500">
              {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
            <motion.button
              onClick={handleCopy}
              whileHover={{ scale: 1.1, backgroundColor: "rgba(255,255,255,0.1)" }}
              whileTap={{ scale: 0.9 }}
              className="p-1.5 rounded-lg transition-colors"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-green-400" />
              ) : (
                <Copy className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300" />
              )}
            </motion.button>
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}

function ThinkingIndicator() {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-4">
      <div className="relative">
        {/* Spinning gradient ring */}
        <motion.div
          className="absolute -inset-1 rounded-xl"
          style={{
            background: "conic-gradient(from 0deg, #4f46e5, #f43f5e, #60a5fa, #4f46e5)",
            padding: "2px",
          }}
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
        >
          <div className="w-full h-full rounded-xl bg-[#0a0f1a]" />
        </motion.div>

        {/* Outer glow pulse */}
        <motion.div
          className="absolute -inset-2 rounded-xl bg-gradient-to-r from-[#4f46e5] to-[#f43f5e] opacity-30 blur-md"
          animate={{ opacity: [0.2, 0.5, 0.2], scale: [0.95, 1.05, 0.95] }}
          transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
        />

        {/* Icon */}
        <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-[#f43f5e] via-[#ec4899] to-[#d946ef] p-[2px]">
          <div className="w-full h-full rounded-xl bg-[#0f172a] flex items-center justify-center">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
            >
              <Brain className="w-5 h-5 text-white" />
            </motion.div>
          </div>
        </div>
      </div>

      {/* Thinking text with animated dots */}
      <div className="px-5 py-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-300 font-medium">Thinking</span>
          <div className="flex items-center gap-0.5">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="text-sm text-slate-300"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{
                  duration: 1.2,
                  repeat: Number.POSITIVE_INFINITY,
                  delay: i * 0.2,
                  ease: "easeInOut",
                }}
              >
                .
              </motion.span>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  )
}