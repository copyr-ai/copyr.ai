import { Nunito_Sans } from "next/font/google";
import "./globals.css";

const nunitoSans = Nunito_Sans({
  subsets: ["latin"],
  variable: "--font-nunito-sans",
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata = {
  metadataBase: new URL('https://copyr.ai'),
  title: "copyr.ai - Copyright clarity, without the chaos",
  description: "Search, verify, and track the rights of creative works; starting with public domain authorship. AI-powered copyright protection tools for creators.",
  keywords: "copyright, public domain, creative works, authorship, legal-tech, creator-economy, rights-management, copyright search, intellectual property",
  authors: [{ name: "copyr.ai" }],
  creator: "copyr.ai",
  publisher: "copyr.ai",
  robots: "index, follow",
  openGraph: {
    title: "copyr.ai - Copyright clarity, without the chaos",
    description: "Search, verify, and track the rights of creative works; starting with public domain authorship. AI-powered copyright protection tools for creators.",
    url: "https://copyr.ai",
    siteName: "copyr.ai",
    type: "website",
    images: [
      {
        url: "/logo.svg",
        width: 800,
        height: 600,
        alt: "copyr.ai - Copyright clarity tools",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "copyr.ai - Copyright clarity, without the chaos",
    description: "Search, verify, and track the rights of creative works; starting with public domain authorship.",
    images: ["/logo.svg"],
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
    apple: "/favicon.ico",
  },
};

export default function RootLayout({ children }) {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "copyr.ai",
    "description": "Search, verify, and track the rights of creative works; starting with public domain authorship. AI-powered copyright protection tools for creators.",
    "url": "https://copyr.ai",
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://copyr.ai/?q={search_term_string}"
      },
      "query-input": "required name=search_term_string"
    },
    "publisher": {
      "@type": "Organization",
      "name": "copyr.ai",
      "url": "https://copyr.ai"
    }
  }

  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#EC4899" />
        <link rel="canonical" href="https://copyr.ai" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      </head>
      <body className={`${nunitoSans.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
