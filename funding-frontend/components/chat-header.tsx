"use client"

import { motion } from "framer-motion"
import { Brain, Zap } from "lucide-react"

export function ChatHeader() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="flex items-center justify-center py-6 px-4"
    >
      <div className="flex items-center gap-3">
        <motion.div className="relative" whileHover={{ scale: 1.05 }} transition={{ type: "spring", stiffness: 400 }}>
          <div className="relative w-12 h-12 rounded-2xl bg-gradient-to-br from-[#4f46e5] via-[#7c3aed] to-[#f43f5e] p-[2px]">
            <div className="w-full h-full rounded-2xl bg-[#0a0f1a] flex items-center justify-center relative overflow-hidden">
              {/* Inner gradient glow */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#4f46e5]/20 to-[#f43f5e]/20" />
              <Brain className="w-6 h-6 text-white relative z-10" />
              {/* Animated corner sparkle */}
              <motion.div
                className="absolute top-1 right-1"
                animate={{ opacity: [0.5, 1, 0.5], scale: [0.8, 1, 0.8] }}
                transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
              >
                <Zap className="w-2.5 h-2.5 text-[#60a5fa]" />
              </motion.div>
            </div>
          </div>
          {/* Glow effect */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[#4f46e5] to-[#f43f5e] opacity-40 blur-xl" />
        </motion.div>

        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">Aura</h1>
          <p className="text-xs text-slate-400">RAG Assistant</p>
        </div>
      </div>
    </motion.header>
  )
}
