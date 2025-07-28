import { motion } from 'framer-motion'
import Head from 'next/head'

export default function Home() {
  return (
    <>
      <Head>
        <title>copyr.ai - Copyright Intelligence Platform</title>
        <meta name="description" content="Premium copyright intelligence infrastructure for creators, publishers, and legal teams" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center space-y-6 max-w-2xl"
        >
          <motion.h1 
            className="text-6xl font-bold text-slate-900 mb-4"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            Hello from <span className="text-blue-600">copyr.ai</span>
          </motion.h1>
          
          <motion.p 
            className="text-xl text-slate-600 mb-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            Premium copyright intelligence infrastructure for creators, publishers, and legal teams
          </motion.p>
          
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.6 }}
          >
            <div className="bg-white rounded-lg p-6 shadow-md">
              <h3 className="font-semibold text-slate-900 mb-2">Data Collection</h3>
              <p className="text-sm text-slate-600">Automated scraping and aggregation from authoritative sources</p>
            </div>
            <div className="bg-white rounded-lg p-6 shadow-md">
              <h3 className="font-semibold text-slate-900 mb-2">Structured Analysis</h3>
              <p className="text-sm text-slate-600">Converting raw data into actionable copyright insights</p>
            </div>
            <div className="bg-white rounded-lg p-6 shadow-md">
              <h3 className="font-semibold text-slate-900 mb-2">API Access</h3>
              <p className="text-sm text-slate-600">RESTful APIs for seamless integration</p>
            </div>
          </motion.div>
          
          <motion.div
            className="mt-8 text-sm text-slate-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8, duration: 0.6 }}
          >
            Frontend: <span className="font-mono">http://localhost:3000</span> | 
            Backend: <span className="font-mono">http://localhost:8000</span>
          </motion.div>
        </motion.div>
      </div>
    </>
  )
}