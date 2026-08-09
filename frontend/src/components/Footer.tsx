import { Link } from 'react-router-dom';
import {
  Phone,
  Mail,
  MapPin,
  Heart,
  Siren,
  ArrowUpRight,
} from 'lucide-react';
import { Logo } from './ui/Logo';

const quickLinks = [
  { label: 'Home', to: '/' },
  { label: 'Take Test', to: '/register/relationship' },
  { label: 'Adult Care', to: '/adult-care' },
  { label: 'Child Care', to: '/child-care' },
  { label: 'AI Assistant', to: '/ai-assistant' },
];

const resourceLinks = [
  { label: 'Hearing Tests Explained', to: '/adult-care' },
  { label: 'Child Hearing Milestones', to: '/child-care' },
  { label: 'About NIEPMD', to: '/about' },
  { label: 'Contact Us', to: '/contact' },
];

export function Footer() {
  return (
    <footer className="mt-24 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
      <div className="container-page py-14">
        <div className="grid gap-10 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <Logo />
            <p className="mt-4 text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-w-sm">
              An AI-powered hearing Take Test assistant helping children and adults identify
              hearing-related concerns and connect with the right care.
            </p>
          </div>

          <div className="lg:col-span-2">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Quick Links</h3>
            <ul className="mt-4 space-y-2.5">
              {quickLinks.map((l) => (
                <li key={l.label}>
                  <Link
                    to={l.to}
                    className="text-sm text-slate-600 hover:text-brand-700 dark:text-slate-400 dark:hover:text-brand-300 inline-flex items-center gap-1 group"
                  >
                    {l.label}
                    <ArrowUpRight size={13} className="opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-2">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Resources</h3>
            <ul className="mt-4 space-y-2.5">
              {resourceLinks.map((l) => (
                <li key={l.label}>
                  <Link
                    to={l.to}
                    className="text-sm text-slate-600 hover:text-brand-700 dark:text-slate-400 dark:hover:text-brand-300 inline-flex items-center gap-1 group"
                  >
                    {l.label}
                    <ArrowUpRight size={13} className="opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Emergency Contact</h3>
            <div className="mt-4 rounded-2xl bg-gradient-to-br from-brand-50 to-purple-50 dark:from-brand-900/30 dark:to-purple-900/30 border border-brand-100 dark:border-brand-900/50 p-5">
              <div className="flex items-center gap-2 text-brand-700 dark:text-brand-300">
                <Siren size={18} />
                <span className="text-sm font-semibold">24/7 Hearing Helpline</span>
              </div>
              <a href="tel:+911800123456" className="mt-2 block text-2xl font-bold text-slate-900 dark:text-white">
                1800-123-456
              </a>
              <ul className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                <li className="flex items-center gap-2">
                  <Mail size={15} className="text-brand-500" />
                  care@niepmd.nic.in
                </li>
                <li className="flex items-center gap-2">
                  <MapPin size={15} className="text-brand-500" />
                  Audiology Wing, City Care Hospital
                </li>
                <li className="flex items-center gap-2">
                  <Phone size={15} className="text-brand-500" />
                  Mon–Sat, 9 AM – 7 PM
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            © {new Date().getFullYear()} NIEPMD Audiology and Speech. All rights reserved.
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 inline-flex items-center gap-1.5">
            Made with <Heart size={12} className="text-pink-500 fill-pink-500" /> for hearing care
          </p>
        </div>
      </div>
    </footer>
  );
}
