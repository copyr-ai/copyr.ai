import Image from "next/image"
import { useState } from "react"

export default function Footer() {
  const [email, setEmail] = useState("")
  const [message, setMessage] = useState("")

  const handleEmailSubmit = (e) => {
    e.preventDefault()
    if (email && message) {
      // Try multiple approaches for better compatibility
      const subject = encodeURIComponent(`Contact from ${email}`)
      const body = encodeURIComponent(`From: ${email}\n\nMessage:\n${message}`)
      const mailtoUrl = `mailto:hello@copyr.ai?subject=${subject}&body=${body}`
      
      try {
        // Primary method: use window.location
        window.location.href = mailtoUrl
      } catch (error) {
        try {
          // Fallback: create a temporary link and click it
          const link = document.createElement('a')
          link.href = mailtoUrl
          link.target = '_blank'
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } catch (fallbackError) {
          // Final fallback: copy email to clipboard and alert user
          navigator.clipboard.writeText('hello@copyr.ai').then(() => {
            alert('Please send your message to: hello@copyr.ai (email copied to clipboard)')
          }).catch(() => {
            alert('Please send your message to: hello@copyr.ai')
          })
        }
      }
      
      setEmail("")
      setMessage("")
    }
  }

  return (
    <footer className="bg-brand-dark text-white py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          {/* Brand Section */}
          <div className="lg:col-span-2">
            <div className="mb-6">
              <Image
                src="/brand-copyr.ai-dark.svg"
                alt="copyr.ai"
                width={150}
                height={45}
                className="h-10 w-auto"
              />
            </div>
            <p className="text-gray-300 text-lg mb-6 max-w-md">
              Simplifying copyright research for creators worldwide. Get clear, reliable information about what you can legally use.
            </p>
            <div className="flex space-x-4">
              <a 
                href="https://linkedin.com/company/copyr-ai" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-brand-pink rounded-full flex items-center justify-center hover:bg-brand-purple transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
              </a>
              <a 
                href="https://www.instagram.com/copyr.ai/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-10 h-10 bg-brand-pink rounded-full flex items-center justify-center hover:bg-brand-purple transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 1.206.056 2.003.24 2.468.403a4.92 4.92 0 011.683 1.01 4.92 4.92 0 011.01 1.683c.163.465.347 1.262.403 2.468.058 1.266.07 1.646.07 4.85s-.012 3.584-.07 4.85c-.056 1.206-.24 2.003-.403 2.468a4.94 4.94 0 01-1.01 1.683 4.92 4.92 0 01-1.683 1.01c-.465.163-1.262.347-2.468.403-1.266.058-1.646.07-4.85.07s-3.584-.012-4.85-.07c-1.206-.056-2.003-.24-2.468-.403a4.92 4.92 0 01-1.683-1.01 4.92 4.92 0 01-1.01-1.683c-.163-.465-.347-1.262-.403-2.468C2.175 15.747 2.163 15.367 2.163 12s.012-3.584.07-4.85c.056-1.206.24-2.003.403-2.468a4.94 4.94 0 011.01-1.683A4.92 4.92 0 015.33 2.636c.465-.163 1.262-.347 2.468-.403C8.416 2.175 8.796 2.163 12 2.163zm0-2.163C8.736 0 8.332.012 7.052.07 5.772.127 4.89.308 4.13.6a7.064 7.064 0 00-2.565 1.684A7.064 7.064 0 00.6 4.13C.308 4.89.127 5.772.07 7.052.012 8.332 0 8.736 0 12c0 3.264.012 3.668.07 4.948.057 1.28.238 2.162.53 2.922a7.064 7.064 0 001.684 2.565 7.064 7.064 0 002.565 1.684c.76.292 1.642.473 2.922.53C8.332 23.988 8.736 24 12 24s3.668-.012 4.948-.07c1.28-.057 2.162-.238 2.922-.53a7.064 7.064 0 002.565-1.684 7.064 7.064 0 001.684-2.565c.292-.76.473-1.642.53-2.922.058-1.28.07-1.684.07-4.948s-.012-3.668-.07-4.948c-.057-1.28-.238-2.162-.53-2.922a7.064 7.064 0 00-1.684-2.565A7.064 7.064 0 0019.87.6c-.76-.292-1.642-.473-2.922-.53C15.668.012 15.264 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zm0 10.162a3.999 3.999 0 110-7.998 3.999 3.999 0 010 7.998zm6.406-11.845a1.44 1.44 0 11-2.88 0 1.44 1.44 0 012.88 0z" />
                </svg>
              </a>
            </div>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Company</h3>
            <ul className="space-y-3">
              <li><a href="#about" className="text-gray-300 hover:text-white transition-colors">About</a></li>
              <li><a href="https://linkedin.com/company/copyr-ai" target="_blank" rel="noopener noreferrer" className="text-gray-300 hover:text-white transition-colors">Connect</a></li>
            </ul>
          </div>

          {/* Connect with Email */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Get in Touch</h3>
            <form onSubmit={handleEmailSubmit} className="space-y-3">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 rounded-md bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-pink"
                placeholder="Enter your email"
                required
              />
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full px-4 py-2 rounded-md bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-pink resize-none"
                placeholder="Enter your message"
                rows="3"
                required
              />
              <button
                type="submit"
                className="w-full px-4 py-2 bg-brand-pink text-white rounded-md hover:bg-brand-purple transition-colors"
              >
                Send Message
              </button>
              <p className="text-xs text-gray-400">We'll respond to your inquiry at the soonest.</p>
            </form>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gray-700 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-gray-400 text-sm mb-4 md:mb-0">
              © 2025 copyr.ai. All rights reserved.
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
