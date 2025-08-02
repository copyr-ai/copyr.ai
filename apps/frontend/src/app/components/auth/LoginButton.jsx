'use client'

import { Button } from '@/app/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'

export default function LoginButton({ className = '' }) {
  const { signInWithGoogle, loading } = useAuth()

  const handleLogin = async () => {
    const { error } = await signInWithGoogle()
    if (error) {
      console.error('Login error:', error)
    }
  }

  return (
    <Button 
      onClick={handleLogin}
      disabled={loading}
      className={`bg-blue-600 hover:bg-blue-700 text-white ${className}`}
    >
      {loading ? 'Loading...' : 'Sign in with Google'}
    </Button>
  )
}