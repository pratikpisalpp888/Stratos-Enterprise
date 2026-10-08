import Link from 'next/link'

export function HeroSection() {
  const stats = [
    "100% RBAC Integrity",
    "100% Attack Defense",
    "89% Faithfulness",
    "4 Access Tiers"
  ]

  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen px-4 sm:px-6 pt-28 sm:pt-32 pb-12">
      {/* Hero Content Box */}
      <div className="relative z-10 flex flex-col items-center max-w-4xl mx-auto text-center">
        {/* Eyebrow Tag */}
        <div className="text-[10px] sm:text-xs uppercase tracking-[0.25em] text-[#191919] font-bold bg-white/90 backdrop-blur-md px-4 py-1.5 rounded-full border border-[#191919]/15 shadow-xs mb-6 animate-eyebrow-pulse">
          INTERNAL AI ASSISTANT
        </div>

        {/* H1 Headline with Smooth Entrance Animation */}
        <h1 className="font-serif text-3xl sm:text-5xl md:text-6xl lg:text-7xl leading-[1.1] tracking-tighter text-[#191919] font-normal animate-title-reveal">
          Your Company&apos;s AI,<br className="hidden sm:block" /> Built for Your Role.
        </h1>

        {/* Sub-headline */}
        <p className="max-w-xl mt-5 sm:mt-6 text-xs sm:text-sm md:text-base text-[#191919]/85 leading-relaxed font-normal">
          Stratos Enterprises&apos; internal AI assistant answers questions, retrieves records, and performs actions — automatically respecting who you are, what department you belong to, and what you&apos;re authorized to see.
        </p>

        {/* CTA Button */}
        <div className="mt-6 sm:mt-8">
          <Link
            href="/login"
            className="inline-block px-7 py-3 bg-[#191919] text-white text-xs sm:text-sm font-medium rounded-lg hover:bg-[#191919]/90 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 shadow-md"
          >
            Get Started
          </Link>
        </div>

        {/* Crisp Glassmorphic Stats Bar */}
        <div className="mt-10 sm:mt-14 w-full max-w-2xl bg-white/85 backdrop-blur-md border border-[#191919]/15 shadow-sm rounded-2xl px-6 py-3.5">
          <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-xs font-semibold text-[#191919]">
            {stats.map((stat, idx) => (
              <div key={stat} className="flex items-center gap-3 sm:gap-6">
                <span className="tracking-tight">{stat}</span>
                {idx < stats.length - 1 && (
                  <span className="text-[#191919]/25 font-bold">|</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
