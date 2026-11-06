// FILE: src/components/layout/Footer.tsx
import { Link } from 'react-router-dom'
import { BookOpen, Github, Twitter, Linkedin } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t border-[#1e2d4a] bg-[#0a0e1a]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-600 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
                <BookOpen size={16} className="text-white" />
              </div>
              <span className="text-lg font-bold gradient-text">LIBRIX AI</span>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed max-w-xs">
              Your intelligent digital library powered by AI. Explore thousands of books and unlock knowledge with smart tools.
            </p>
            <div className="flex items-center gap-3 mt-5">
              <SocialLink href="https://github.com" icon={<Github size={16} />} />
              <SocialLink href="https://twitter.com" icon={<Twitter size={16} />} />
              <SocialLink href="https://linkedin.com" icon={<Linkedin size={16} />} />
            </div>
          </div>

          {/* Links */}
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Product</p>
            <ul className="flex flex-col gap-2.5">
              <FooterLink to="/library" label="Library" />
              <FooterLink to="/ai" label="AI Assistant" />
              <FooterLink to="/dashboard" label="Dashboard" />
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Company</p>
            <ul className="flex flex-col gap-2.5">
              <FooterLink to="/" label="About" />
              <FooterLink to="/" label="Contact" />
              <FooterLink to="/" label="Terms of Service" />
              <FooterLink to="/" label="Privacy Policy" />
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-[#1e2d4a] flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-slate-600">
            © 2024 LIBRIX AI. All rights reserved.
          </p>
          <p className="text-xs text-slate-600">
            Built with ❤️ for knowledge seekers worldwide
          </p>
        </div>
      </div>
    </footer>
  )
}

function FooterLink({ to, label }: { to: string; label: string }) {
  return (
    <li>
      <Link to={to} className="text-sm text-slate-500 hover:text-slate-300 transition-colors">
        {label}
      </Link>
    </li>
  )
}

function SocialLink({ href, icon }: { href: string; icon: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="w-8 h-8 rounded-lg border border-[#1e2d4a] flex items-center justify-center text-slate-500 hover:text-white hover:border-purple-500/40 hover:bg-purple-500/10 transition-all"
    >
      {icon}
    </a>
  )
}

