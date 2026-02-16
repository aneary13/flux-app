import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 bg-[#f7f6f3]">
      <h1 className="text-4xl font-bold text-neutral-900">FLUX</h1>
      <div className="mt-8">
        <Link href="/login" className={buttonVariants({ size: "lg" })}>
          Login
        </Link>
      </div>
    </main>
  );
}
