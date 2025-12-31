"use client"

import type React from "react"
import { useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Mic, Loader2 } from "lucide-react"

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (e: React.FormEvent) => void
  isLoading: boolean
}

export function ChatInput({ value, onChange, onSubmit, isLoading }: ChatInputProps) {
  const [isFocused, setIsFocused] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const [isHovered, setIsHovered] = useState(false)
  const [micHovered, setMicHovered] = useState(false)
  const [sendHovered, setSendHovered] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSubmit(e)
    }
  }

  // 🎤 REAL VOICE RECOGNITION LOGIC ADDED HERE
  const toggleListening = () => {
    if (isListening) {
      setIsListening(false)
      return
    }

    // Check if browser supports speech recognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    
    if (!SpeechRecognition) {
      alert("Your browser does not support Voice Input. Try Chrome or Edge.")
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.continuous = false
    recognition.interimResults = false

    setIsListening(true)

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      onChange(transcript) // Puts text into input box
      setIsListening(false)
    }

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error", event.error)
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.start()
  }

  return (
    <div className="px-4 pb-6 pt-2">
      <form onSubmit={onSubmit}>
        <div
          ref={containerRef}
          onMouseMove={handleMouseMove}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className="relative max-w-3xl mx-auto"
        >
          <motion.div
            className="absolute -inset-4 rounded-3xl pointer-events-none"
            animate={{
              opacity: isHovered || isFocused ? 0.8 : 0,
            }}
            transition={{ duration: 0.4 }}
            style={{
              background: `radial-gradient(350px circle at ${mousePos.x}px ${mousePos.y}px, rgba(79, 70, 229, 0.2), rgba(244, 63, 94, 0.15), transparent 60%)`,
            }}
          />

          <div className="absolute -inset-[1px] rounded-2xl overflow-hidden">
            <motion.div
              className="absolute inset-0"
              animate={{
                opacity: isFocused ? 1 : isHovered ? 0.7 : 0.3,
              }}
              transition={{ duration: 0.3 }}
            >
              <motion.div
                className="absolute -inset-[100%] w-[300%] h-[300%]"
                style={{
                  backgroundImage:
                    "linear-gradient(90deg, #4f46e5, #f43f5e, #60a5fa, #4f46e5, #f43f5e, #60a5fa, #4f46e5)",
                  backgroundSize: "50% 100%",
                }}
                animate={{
                  x: ["0%", "-33.33%"],
                }}
                transition={{
                  duration: 3,
                  repeat: Number.POSITIVE_INFINITY,
                  ease: "linear",
                }}
              />
            </motion.div>
            <div className="absolute inset-[1px] rounded-2xl bg-[#0f1420]" />
          </div>

          <div className="relative flex items-center bg-[#0f1420]/90 backdrop-blur-xl rounded-2xl overflow-hidden">
            <textarea
              ref={inputRef}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Message Aura..."
              disabled={isLoading}
              rows={1}
              className="flex-1 px-5 py-4 bg-transparent text-white placeholder:text-slate-500 focus:outline-none resize-none text-sm leading-relaxed max-h-32"
              style={{ minHeight: "56px" }}
            />

            <div className="flex items-center gap-3 px-3 py-2">
              <motion.button
                type="button"
                onClick={toggleListening}
                onMouseEnter={() => setMicHovered(true)}
                onMouseLeave={() => setMicHovered(false)}
                whileTap={{ scale: 0.92 }}
                className="relative w-11 h-11 rounded-full overflow-visible"
              >
                <div
                  className="absolute -inset-2 rounded-full pointer-events-none transition-all duration-500 ease-out"
                  style={{
                    opacity: isListening ? 0.8 : micHovered ? 0.5 : 0,
                    transform: isListening ? "scale(1.1)" : "scale(1)",
                    background:
                      "radial-gradient(circle, rgba(244, 63, 94, 0.5), rgba(236, 72, 153, 0.3), transparent 70%)",
                    filter: "blur(8px)",
                  }}
                />

                <div
                  className="absolute inset-0 rounded-full transition-all duration-300 ease-out"
                  style={{
                    background: isListening
                      ? "linear-gradient(to bottom right, #f43f5e, #db2777)"
                      : micHovered
                        ? "linear-gradient(to bottom right, rgba(244, 63, 94, 0.2), rgba(219, 39, 119, 0.15))"
                        : "rgba(30, 41, 59, 0.8)",
                    backdropFilter: "blur(12px)",
                  }}
                />

                <div
                  className="absolute inset-0 rounded-full pointer-events-none transition-opacity duration-300"
                  style={{
                    opacity: isListening ? 1 : micHovered ? 0.6 : 0,
                    background:
                      "linear-gradient(135deg, rgba(244, 63, 94, 0.5), rgba(236, 72, 153, 0.3), rgba(168, 85, 247, 0.2))",
                    padding: "1px",
                    WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
                    WebkitMaskComposite: "xor",
                    maskComposite: "exclude",
                  }}
                />

                <div
                  className="absolute inset-[1px] rounded-full bg-gradient-to-b from-white/10 to-transparent pointer-events-none transition-opacity duration-300"
                  style={{ opacity: micHovered || isListening ? 1 : 0 }}
                />

                {isListening && (
                  <>
                    <div
                      className="absolute inset-0 rounded-full border-2 border-rose-400 pointer-events-none animate-[ripple_1.5s_ease-out_infinite]"
                      style={{ animationDelay: "0s" }}
                    />
                    <div
                      className="absolute inset-0 rounded-full border border-pink-400 pointer-events-none animate-[ripple_1.5s_ease-out_infinite]"
                      style={{ animationDelay: "0.3s" }}
                    />
                    <div
                      className="absolute inset-0 rounded-full border border-purple-400/50 pointer-events-none animate-[ripple_1.5s_ease-out_infinite]"
                      style={{ animationDelay: "0.6s" }}
                    />
                  </>
                )}

                <div className="relative z-10 flex items-center justify-center w-full h-full">
                  <AnimatePresence mode="wait">
                    {isListening ? (
                      <motion.div
                        key="waveform"
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.5 }}
                        className="flex items-center justify-center gap-[3px]"
                      >
                        {[0, 1, 2, 3, 4].map((i) => (
                          <div
                            key={i}
                            className="w-[3px] rounded-full bg-white animate-[waveform_0.8s_linear_infinite]"
                            style={{
                              animationDelay: `${i * 0.1}s`,
                            }}
                          />
                        ))}
                      </motion.div>
                    ) : (
                      <motion.div
                        key="mic"
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.5 }}
                        whileHover={{ rotate: [0, -10, 10, 0] }}
                        transition={{ rotate: { duration: 0.4 } }}
                      >
                        <Mic
                          className={`w-[18px] h-[18px] transition-colors duration-300 ${
                            micHovered ? "text-rose-400" : "text-slate-400"
                          }`}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.button>

              <motion.button
                type="submit"
                disabled={isLoading || !value.trim()}
                onMouseEnter={() => setSendHovered(true)}
                onMouseLeave={() => setSendHovered(false)}
                whileTap={{ scale: 0.92 }}
                className="relative w-11 h-11 rounded-full text-white disabled:opacity-30 disabled:cursor-not-allowed overflow-visible"
              >
                <motion.div
                  className="absolute -inset-2 rounded-full"
                  animate={{
                    opacity: sendHovered && !isLoading && value.trim() ? 0.8 : 0,
                  }}
                  transition={{ duration: 0.3 }}
                  style={{
                    background:
                      "radial-gradient(circle, rgba(79, 70, 229, 0.6), rgba(99, 102, 241, 0.4), transparent 70%)",
                    filter: "blur(12px)",
                  }}
                />

                <motion.div
                  className="absolute inset-0 rounded-full overflow-hidden"
                  style={{
                    background: "linear-gradient(135deg, #4f46e5, #6366f1, #818cf8, #4f46e5)",
                    backgroundSize: "300% 300%",
                  }}
                  animate={{
                    backgroundPosition: sendHovered ? ["0% 0%", "100% 100%"] : "0% 0%",
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: sendHovered ? Number.POSITIVE_INFINITY : 0,
                    repeatType: "reverse",
                  }}
                />

                <div className="absolute inset-0 rounded-full bg-gradient-to-b from-white/20 via-transparent to-black/20" />

                <motion.div
                  className="absolute inset-0 rounded-full"
                  animate={{
                    opacity: sendHovered ? 1 : 0.5,
                  }}
                  style={{
                    background:
                      "linear-gradient(135deg, rgba(255,255,255,0.3), transparent 50%, rgba(255,255,255,0.1))",
                    padding: "1px",
                    WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
                    WebkitMaskComposite: "xor",
                    maskComposite: "exclude",
                  }}
                />

                <motion.div className="absolute inset-0 rounded-full overflow-hidden" initial={false}>
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -skew-x-12"
                    initial={{ x: "-150%" }}
                    animate={{ x: sendHovered ? "150%" : "-150%" }}
                    transition={{ duration: 0.6, ease: "easeInOut" }}
                  />
                </motion.div>

                <div className="relative z-10 flex items-center justify-center w-full h-full">
                  <AnimatePresence mode="wait">
                    {isLoading ? (
                      <motion.div
                        key="loading"
                        initial={{ opacity: 0, rotate: -90 }}
                        animate={{ opacity: 1, rotate: 0 }}
                        exit={{ opacity: 0, rotate: 90 }}
                      >
                        <Loader2 className="w-[18px] h-[18px] animate-spin" />
                      </motion.div>
                    ) : (
                      <motion.div
                        key="send"
                        initial={{ opacity: 0, x: -5 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 5 }}
                        whileHover={{ x: 2, y: -2 }}
                        transition={{ type: "spring", stiffness: 400 }}
                      >
                        <Send className="w-[18px] h-[18px]" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.button>
            </div>
          </div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center text-xs text-slate-500 mt-3"
          >
            Aura can make mistakes. Verify important information.
          </motion.p>
        </div>
      </form>
    </div>
  )
}