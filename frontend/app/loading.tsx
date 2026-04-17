export default function Loading() {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-7xl items-center px-4 py-12 sm:px-8">
      <div className="w-full rounded-[32px] border border-[color:var(--line)] bg-white/4 p-8">
        <div className="h-4 w-36 animate-pulse rounded-full bg-white/10" />
        <div className="mt-6 h-12 w-full max-w-2xl animate-pulse rounded-3xl bg-white/8" />
        <div className="mt-4 h-5 w-full max-w-3xl animate-pulse rounded-full bg-white/6" />
        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          <div className="h-40 animate-pulse rounded-[28px] bg-white/6" />
          <div className="h-40 animate-pulse rounded-[28px] bg-white/6" />
          <div className="h-40 animate-pulse rounded-[28px] bg-white/6" />
        </div>
      </div>
    </div>
  );
}
