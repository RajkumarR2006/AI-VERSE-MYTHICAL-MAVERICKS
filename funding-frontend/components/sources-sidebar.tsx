"use client"

import { motion } from "framer-motion"
import { X, ExternalLink } from "lucide-react"
import type { Source } from "./chat-interface"

interface SourcesSidebarProps {
  sources: Source[]
  onClose: () => void
}

export function SourcesSidebar({ sources, onClose }: SourcesSidebarProps) {
  return (
    <motion.aside
      initial={{ x: 400, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 400, opacity: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="w-80 border-l border-white/10 bg-[#0f1420]/80 backdrop-blur-xl flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-gradient-to-r from-[#4f46e5] to-[#f43f5e]" />
          <h3 className="text-sm font-medium text-white">Sources</h3>
          <span className="text-xs text-slate-500">({sources.length})</span>
        </div>
        <motion.button
          onClick={onClose}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
        >
          <X className="w-4 h-4 text-slate-400" />
        </motion.button>
      </div>

      {/* Sources list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {sources.map((source, index) => (
          <SourceCard key={index} source={source} index={index} />
        ))}
      </div>
    </motion.aside>
  )
}

function SourceCard({ source, index }: { source: Source; index: number }) {
  const getFileType = (filename: string) => {
    if (filename.endsWith(".pdf")) return { type: "PDF", color: "#f43f5e" }
    if (filename.endsWith(".csv")) return { type: "CSV", color: "#60a5fa" }
    if (filename.endsWith(".txt")) return { type: "TXT", color: "#4f46e5" }
    return { type: "DOC", color: "#8b5cf6" }
  }

  const { type, color } = getFileType(source.source)

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ scale: 1.02 }}
      className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all cursor-pointer group"
    >
      <div className="flex items-start gap-3 mb-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold text-white"
          style={{ backgroundColor: `${color}20`, color }}
        >
          {type}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-white truncate">{source.source}</h4>
          <p className="text-xs text-slate-500">Source #{index + 1}</p>
        </div>
        <motion.div className="opacity-0 group-hover:opacity-100 transition-opacity" whileHover={{ scale: 1.2 }}>
          <ExternalLink className="w-4 h-4 text-slate-400" />
        </motion.div>
      </div>

      <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">{source.content}</p>

      {/* Relevance indicator */}
      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-white/5">
        <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
        <span className="text-xs text-slate-500">High relevance</span>
      </div>
    </motion.div>
  )
}
