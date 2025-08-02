'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { supabaseClient } from '../../lib/supabase'

export default function AuthCallback() {
  const router = useRouter()

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        const { data, error } = await supabaseClient.auth.getSession()
        
        if (error) {
          console.error('Auth callback error:', error)
          router.push('/auth/error')
          return
        }

        if (data.session) {
          // Successfully authenticated
          router.push('/search')
        } else {
          // No session found
          router.push('/')
        }
      } catch (error) {
        console.error('Auth callback error:', error)
        router.push('/auth/error')
      }
    }

    handleAuthCallback()
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-brand-pink mx-auto"></div>
        <p className="mt-4 text-gray-600">Completing authentication...</p>
      </div>
    </div>
  )
}