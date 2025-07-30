'use client'

import { motion } from "framer-motion"
import { Button } from "./components/ui/button"
import Link from "next/link"
import Image from "next/image"
import { useEffect, useState } from "react"

export default function NotFound() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [isHovering, setIsHovering] = useState(false)
  const [isLaptopView, setIsLaptopView] = useState(false)
  
  // Check if screen is laptop size for cursor effects
  useEffect(() => {
    const checkScreenSize = () => {
      setIsLaptopView(window.innerWidth >= 1024) // lg breakpoint
    }
    
    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])
  
  // Mouse tracking effect - only on laptop screens
  useEffect(() => {
    if (!isLaptopView) return
    
    const updateMousePosition = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY })
    }
    
    const handleMouseEnter = () => setIsHovering(true)
    const handleMouseLeave = () => setIsHovering(false)
    
    window.addEventListener('mousemove', updateMousePosition)
    
    // Add hover listeners to interactive elements
    const interactiveElements = document.querySelectorAll('button, a, [role="button"]')
    interactiveElements.forEach(el => {
      el.addEventListener('mouseenter', handleMouseEnter)
      el.addEventListener('mouseleave', handleMouseLeave)
    })
    
    return () => {
      window.removeEventListener('mousemove', updateMousePosition)
      interactiveElements.forEach(el => {
        el.removeEventListener('mouseenter', handleMouseEnter)
        el.removeEventListener('mouseleave', handleMouseLeave)
      })
    }
  }, [isLaptopView])

  return (
    <div className="grainy-bg min-h-screen overflow-x-hidden relative flex items-center justify-center">
      {/* Custom Cursor - only on laptop screens */}
      {isLaptopView && (
        <>
          <div 
            className={`custom-cursor ${isHovering ? 'hover' : ''}`}
            style={{
              left: mousePosition.x,
              top: mousePosition.y,
            }}
          />
          
          {/* Mouse Blur Effect */}
          <div 
            className="mouse-blur"
            style={{
              left: mousePosition.x - 100,
              top: mousePosition.y - 100,
              width: '200px',
              height: '200px',
            }}
          />
        </>
      )}

      {/* 404 Content */}
      <div className="text-center px-4 max-w-2xl mx-auto">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="mb-12"
        >
          <Link href="/" className="inline-block">
            <Image 
              src="/brand-copyr.ai-light.svg" 
              alt="copyr.ai" 
              width={200}
              height={60}
              className="h-16 w-auto mx-auto hover:scale-105 transition-transform duration-300"
              priority
            />
          </Link>
        </motion.div>

        {/* 404 Animation */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mb-8"
        >
          <h1 className="text-8xl md:text-9xl font-bold gradient-text-primary mb-4">
            404
          </h1>
        </motion.div>

        {/* Error Message */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mb-8"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-brand-dark mb-4">
            Page Not Found
          </h2>
          <p className="text-xl text-gray-600 leading-relaxed max-w-lg mx-auto">
            Oops! The page you&apos;re looking for seems to have wandered into the public domain. 
            Let&apos;s get you back to copyright clarity.
          </p>
        </motion.div>

        {/* Floating Elements Animation */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.7 }}
          className="absolute inset-0 pointer-events-none overflow-hidden"
        >
          {/* Floating copyright symbols */}
          <motion.div
            animate={{ 
              y: [0, -20, 0],
              rotate: [0, 5, -5, 0]
            }}
            transition={{ 
              duration: 4, 
              repeat: Infinity, 
              ease: "easeInOut" 
            }}
            className="absolute top-1/4 left-1/4 text-4xl text-brand-pink/20"
          >
            ©
          </motion.div>
          
          <motion.div
            animate={{ 
              y: [0, 20, 0],
              rotate: [0, -3, 3, 0]
            }}
            transition={{ 
              duration: 3, 
              repeat: Infinity, 
              ease: "easeInOut",
              delay: 1
            }}
            className="absolute top-1/3 right-1/4 text-3xl text-brand-purple/20"
          >
            ℗
          </motion.div>
          
          <motion.div
            animate={{ 
              y: [0, -15, 0],
              rotate: [0, 4, -4, 0]
            }}
            transition={{ 
              duration: 5, 
              repeat: Infinity, 
              ease: "easeInOut",
              delay: 2
            }}
            className="absolute bottom-1/3 left-1/3 text-5xl text-brand-pink/15"
          >
            ®
          </motion.div>
        </motion.div>

        {/* CTA Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
        >
          <Link href="/">
            <Button
              size="lg"
              className="bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white font-semibold px-12 py-4 text-lg rounded-full shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 inline-flex items-center gap-2"
            >
              <svg 
                className="w-5 h-5" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M10 19l-7-7m0 0l7-7m-7 7h18" 
                />
              </svg>
              Back to Home
            </Button>
          </Link>
        </motion.div>
      </div>
    </div>
  )
}
