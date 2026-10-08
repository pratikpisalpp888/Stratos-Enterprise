import { Navbar } from '@/components/navbar'
import { HeroSection } from '@/components/hero-section'
import { BoomerangVideoBg } from '@/components/boomerang-video-bg'

export default function Page() {
  return (
    <main className="min-h-screen bg-white overflow-x-hidden">
      <BoomerangVideoBg />
      <Navbar />
      <HeroSection />
    </main>
  )
}
