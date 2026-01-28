import { Video, Sparkles, Clock, ArrowRight } from "lucide-react";

export default function Home() {
    return (
        <div className="max-w-6xl mx-auto flex flex-col gap-12">
            {/* Header */}
            <section className="flex flex-col gap-4">
                <h2 className="text-4xl font-extrabold tracking-tight">Dashboard</h2>
                <p className="text-white/60 text-lg">Manage your automated content generation pipeline.</p>
            </section>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-blue-400">
                        <Video size={18} />
                        <span className="text-xs font-semibold uppercase tracking-wider">Total Videos</span>
                    </div>
                    <span className="text-3xl font-bold">128</span>
                </div>
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-purple-400">
                        <Sparkles size={18} />
                        <span className="text-xs font-semibold uppercase tracking-wider">Generated Today</span>
                    </div>
                    <span className="text-3xl font-bold">12</span>
                </div>
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-orange-400">
                        <Clock size={18} />
                        <span className="text-xs font-semibold uppercase tracking-wider">Queue Status</span>
                    </div>
                    <span className="text-3xl font-bold">Idle</span>
                </div>
            </div>

            {/* Recent Activity */}
            <section className="flex flex-col gap-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-bold">Recent Videos</h3>
                    <button className="flex items-center gap-2 text-sm text-blue-400 font-medium hover:underline">
                        View All <ArrowRight size={16} />
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="group relative rounded-xl overflow-hidden aspect-[9/16] bg-white/5 border border-white/10 flex items-center justify-center">
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                <span className="text-sm font-medium">Video Topic {i}</span>
                                <span className="text-xs text-white/60">2 hours ago</span>
                            </div>
                            <Video className="text-white/20" size={48} />
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
}
