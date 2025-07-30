'use client'

import Image from "next/image"
import { motion } from "framer-motion"
import { Button } from "../components/ui/button"
import { useEffect, useState } from "react"

export default function Navbar() {
  const [isHidden, setIsHidden] = useState(false)
  
  useEffect(() => {
    const handleScroll = () => {
      const macbookContainer = document.getElementById('survey-container')
      if (macbookContainer) {
        const rect = macbookContainer.getBoundingClientRect()
        const viewportHeight = window.innerHeight
        const scrollY = window.scrollY
        
        // Only hide navbar when:
        // 1. We're not at the very top (scrollY > 100)
        // 2. AND the macbook is prominently in view (center 50% of viewport)
        const atTop = scrollY < 100
        const macbookInCenter = rect.top < viewportHeight * 0.6 && rect.bottom > viewportHeight * 0.4
        
        setIsHidden(!atTop && macbookInCenter)
      }
    }

    window.addEventListener('scroll', handleScroll)
    // Run once on mount to set initial state
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({ 
      top: 0, 
      behavior: 'smooth' 
    })
  }

  return (
    <motion.nav 
      initial={{ opacity: 0, y: -20 }}
      animate={{ 
        opacity: isHidden ? 0 : 1, 
        y: isHidden ? -20 : 0 
      }}
      transition={{ duration: 0.3 }}
      className="fixed top-6 left-1/2 transform -translate-x-1/2 z-50 bg-white/90 backdrop-blur-md rounded-full shadow-lg border border-gray-200 overflow-visible"
    >
      <div className="flex items-center justify-between px-8 py-4">
        {/* Logo */}
        <div className="flex items-center cursor-pointer hover:opacity-80 transition-opacity" onClick={scrollToTop}>
          <Image
            src="/brand-copyr.ai-light.svg"
            alt="copyr.ai"
            width={120}
            height={36}
            className="h-10 w-auto sm:h-12 md:h-10 lg:h-8"
            priority
          />
        </div>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-8 mx-12">
          <a href="#features" className="text-gray-600 hover:text-gray-900 hover:font-semibold font-medium transition-all duration-200">Features</a>
          <a href="#about" className="text-gray-600 hover:text-gray-900 hover:font-semibold font-medium transition-all duration-200">About</a>
          <a 
            href="https://linkedin.com/company/copyr-ai" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-gray-900 hover:font-semibold font-medium transition-all duration-200"
          >
            Connect
          </a>
        </div>

      </div>
    </motion.nav>
  )
}
