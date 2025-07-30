'use client'

import Image from "next/image"
import { motion } from "framer-motion"
import { Button } from "../components/ui/button"
import { useEffect, useState } from "react"
import Navbar from "./Navbar"
import Footer from "./Footer"

export default function HeroSection({ children }) {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [isHovering, setIsHovering] = useState(false)
  const [isOverFooter, setIsOverFooter] = useState(false)
  
  // Simple mouse tracking for custom cursor
  useEffect(() => {
    const updateMousePosition = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY })
      
      // Check if cursor is over footer
      const footerElement = document.querySelector('footer')
      if (footerElement) {
        const footerRect = footerElement.getBoundingClientRect()
        const isInFooter = e.clientY >= footerRect.top && 
                          e.clientY <= footerRect.bottom &&
                          e.clientX >= footerRect.left && 
                          e.clientX <= footerRect.right
        setIsOverFooter(isInFooter) 
      }
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
  }, [])
  
  return (
    <div className="grainy-bg min-h-screen overflow-x-hidden relative">
      {/* Custom Cursor */}
      <div 
        className={`custom-cursor ${isHovering ? 'hover' : ''} ${isOverFooter ? 'footer' : ''}`}
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
      
      {/* Navbar */}
      <Navbar />

      {/* Hero Section */}
      <div className="pt-32 pb-20 px-4 max-w-7xl mx-auto">
        <div className="max-w-4xl mx-auto text-center">
          
          {/* Brand Logo + Big Hero Text in One Line */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="mb-8"
          >
            <div className="flex items-center justify-center gap-4">
              {/* <Image
                src="/brand-copyr.ai-light.svg"
                alt="copyr.ai"
                width={200}
                height={60}
                className="h-14 w-auto flex-shrink-0"
                priority
              /> */}
              {/* <span className="text-5xl text-gray-400 font-light flex-shrink-0">-</span> */}
              <h1 className="text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold text-brand-dark leading-normal">
                <span className="gradient-text-copyright">Copyright</span>{" "}
                <span className="gradient-text-clarity">clarity</span>, without the chaos.
              </h1>
            </div>
          </motion.div>

          {/* Description */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="text-xl md:text-2xl text-gray-600 leading-relaxed max-w-4xl mx-auto mb-12"
          >
            Search, verify, and track the rights of creative works; starting with public domain authorship.
          </motion.p>

          {/* Hero Highlight Badge + CTA Button Side by Side */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex items-center justify-center gap-6 flex-wrap"
          >
            {/* Hero Highlight Badge */}
            <div className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-brand-pink/10 to-brand-purple/10 border border-brand-pink/20 rounded-full">
              <span className="text-brand-pink font-semibold text-sm tracking-wide">
                ✨ Copyright has never been so easy
              </span>
            </div>

          </motion.div>
        </div>
      </div>

      {/* Survey Content */}
      <div className="px-4 max-w-7xl mx-auto mb-20">
        <div className="max-w-4xl mx-auto">
          <div id="survey-container">
            {children}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <motion.section
        id="features"
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
        className="py-20 px-4 max-w-7xl mx-auto"
      >
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-brand-dark mb-6">
            What We <span className="gradient-text-primary">Offer</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Comprehensive copyright solutions designed to simplify your creative workflow
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            viewport={{ once: true }}
            className="bg-white/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 hover:shadow-lg transition-all duration-300"
          >
            <div className="w-12 h-12 bg-gradient-to-r from-brand-pink to-brand-purple rounded-lg mb-6 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-brand-dark mb-4">Smart Search & Verification</h3>
            <p className="text-gray-600">
              Instantly search and verify the copyright status of creative works with our comprehensive database and AI-powered analysis.
            </p>
          </motion.div>

          {/* Feature 2 */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            viewport={{ once: true }}
            className="bg-white/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 hover:shadow-lg transition-all duration-300"
          >
            <div className="w-12 h-12 bg-gradient-to-r from-brand-pink to-brand-purple rounded-lg mb-6 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-brand-dark mb-4">Public Domain Database</h3>
            <p className="text-gray-600">
              Access our curated database of public domain works, starting with authorship and expanding to visual and audio content.
            </p>
          </motion.div>

          {/* Feature 3 */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            viewport={{ once: true }}
            className="bg-white/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 hover:shadow-lg transition-all duration-300"
          >
            <div className="w-12 h-12 bg-gradient-to-r from-brand-pink to-brand-purple rounded-lg mb-6 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-brand-dark mb-4">Real-time Tracking</h3>
            <p className="text-gray-600">
              Monitor copyright status changes and receive notifications when works enter the public domain or status updates occur.
            </p>
          </motion.div>

          {/* Feature 4 */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            viewport={{ once: true }}
            className="bg-white/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 hover:shadow-lg transition-all duration-300"
          >
            <div className="w-12 h-12 bg-gradient-to-r from-brand-pink to-brand-purple rounded-lg mb-6 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-brand-dark mb-4">Legal Documentation</h3>
            <p className="text-gray-600">
              Generate proper citations, licensing documentation, and usage rights certificates for your creative projects.
            </p>
          </motion.div>

          {/* Feature 5 */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            viewport={{ once: true }}
            className="bg-white/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 hover:shadow-lg transition-all duration-300"
          >
            <div className="w-12 h-12 bg-gradient-to-r from-brand-pink to-brand-purple rounded-lg mb-6 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-brand-dark mb-4">Team Collaboration</h3>
            <p className="text-gray-600">
              Share research, maintain team libraries, and collaborate on copyright clearance with built-in team management tools.
            </p>
          </motion.div>

          {/* Feature 6 */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            viewport={{ once: true }}
            className="bg-white/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 hover:shadow-lg transition-all duration-300"
          >
            <div className="w-12 h-12 bg-gradient-to-r from-brand-pink to-brand-purple rounded-lg mb-6 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-brand-dark mb-4">Analytics & Insights</h3>
            <p className="text-gray-600">
              Get detailed analytics on your copyright research, usage patterns, and cost savings from using public domain content.
            </p>
          </motion.div>
        </div>
      </motion.section>

      {/* About Section */}
      <motion.section
        id="about"
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        viewport={{ once: true }}
        className="py-20 px-4 max-w-7xl mx-auto"
      >
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-brand-dark mb-6">
              About <span className="gradient-text-primary">copyr.ai</span>
            </h2>
            <div className="space-y-6 text-lg text-gray-600">
              <p>
                We're building the future of copyright clarity. In a world where creative works are increasingly digital and global, understanding copyright status shouldn't be a barrier to innovation.
              </p>
              <p>
                Our mission is to democratize access to copyright information, starting with public domain authorship and expanding to all forms of creative content. We believe that when creators have clear, reliable information about what they can legally use, they can focus on what they do best; creating.
              </p>
              <p>
                Founded by a team of legal experts, technologists, and creative professionals, copyr.ai combines deep copyright knowledge with cutting-edge AI to make copyright research as simple as a search query.
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            viewport={{ once: true }}
            className="relative"
          >
            <div className="bg-gradient-to-br from-brand-pink/10 to-brand-purple/10 rounded-3xl p-8 border border-gray-200">
              <div className="space-y-6">
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-brand-pink rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-semibold text-brand-dark mb-2">Comprehensive Research</h4>
                    <p className="text-gray-600">We've analyzed millions of works to build the most comprehensive copyright database available.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-brand-purple rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-semibold text-brand-dark mb-2">AI-Powered Accuracy</h4>
                    <p className="text-gray-600">Our machine learning algorithms continuously improve accuracy and identify new public domain works.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-brand-pink rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-semibold text-brand-dark mb-2">Legal Compliance</h4>
                    <p className="text-gray-600">Built with legal experts to ensure all recommendations meet current copyright law standards.</p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.section>

      {/* Footer */}
      <Footer />
    </div>
  )
}
