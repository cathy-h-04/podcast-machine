import { useState, useEffect } from "react";
import { Link } from "react-router";
import { motion } from "framer-motion";

// Types for our podcast data
type Podcast = {
  id: string;
  title: string;
  format: "debate" | "podcast" | "duck";
  createdAt: string;
  duration: number; // in seconds
  audioUrl: string;
};

export function meta() {
  return [
    { title: "My Podcasts | Claude Yap" },
    {
      name: "description",
      content: "View and manage your AI-generated podcasts",
    },
  ];
}

export default function Dashboard() {
  const [podcasts, setPodcasts] = useState<Podcast[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(
    null
  );

  // Fetch podcasts from the server
  useEffect(() => {
    const fetchPodcasts = async () => {
      try {
        setIsLoading(true);

        // Fetch podcasts from the backend API
        const response = await fetch("http://localhost:5111/api/podcasts");
        if (!response.ok) {
          throw new Error(
            `Failed to fetch podcasts: ${response.status} ${response.statusText}`
          );
        }

        const data = await response.json();
        setPodcasts(data.podcasts || []);
        setIsLoading(false);
      } catch (err) {
        console.error("Error fetching podcasts:", err);
        setError("Failed to load podcasts. Please try again later.");
        setIsLoading(false);

        // Use mock data as fallback in case of error
        const mockPodcasts: Podcast[] = [
          {
            id: "1",
            title: "AI Ethics Discussion",
            format: "debate",
            createdAt: "2025-04-15T10:30:00Z",
            duration: 720, // 12 minutes
            audioUrl: "#",
          },
          {
            id: "2",
            title: "Introduction to Machine Learning",
            format: "duck",
            createdAt: "2025-04-10T14:45:00Z",
            duration: 900, // 15 minutes
            audioUrl: "#",
          },
        ];
        setPodcasts(mockPodcasts);
      }
    };

    fetchPodcasts();

    // Cleanup function for audio
    return () => {
      if (audioElement) {
        audioElement.pause();
        audioElement.src = "";
      }
    };
  }, []);

  // Handle playing/pausing podcasts
  const togglePlayPause = (podcast: Podcast) => {
    if (currentlyPlaying === podcast.id) {
      // Pause current audio
      if (audioElement) {
        audioElement.pause();
      }
      setCurrentlyPlaying(null);
    } else {
      // Stop any currently playing audio
      if (audioElement) {
        audioElement.pause();
      }

      // Create and play new audio
      const audio = new Audio(podcast.audioUrl);
      audio.play().catch((err) => {
        console.error("Error playing audio:", err);
        setError("Failed to play audio. The file may be missing or corrupted.");
      });

      setAudioElement(audio);
      setCurrentlyPlaying(podcast.id);

      // Auto-reset when finished
      audio.onended = () => {
        setCurrentlyPlaying(null);
      };
    }
  };

  // Format podcast duration (seconds to mm:ss)
  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
  };

  // Format creation date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(date);
  };

  // Get icon for podcast format
  const getFormatIcon = (format: "debate" | "podcast" | "duck") => {
    switch (format) {
      case "debate":
        return "🎭";
      case "podcast":
        return "🎙️";
      case "duck":
        return "🦆";
      default:
        return "🎧";
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6">
        <div className="container mx-auto max-w-6xl">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Link to="/" className="flex items-center">
                <motion.div
                  initial={{ rotate: -10 }}
                  animate={{ rotate: 10 }}
                  transition={{
                    duration: 0.5,
                    repeat: Infinity,
                    repeatType: "reverse",
                  }}
                  className="text-3xl"
                >
                  🎧
                </motion.div>
                <h1 className="text-2xl font-bold ml-2">Claude Yap</h1>
              </Link>
            </div>
            <Link
              to="/create"
              className="px-4 py-2 bg-white/20 hover:bg-white/30 transition rounded-lg text-sm font-medium"
            >
              Create New Podcast
            </Link>
          </div>
          <h2 className="text-3xl font-bold mt-6 mb-2">My Podcasts</h2>
          <p className="text-indigo-100">
            Manage and listen to your AI-generated podcasts
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto max-w-6xl px-4 py-8">
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
            <p>{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-2 text-sm font-medium underline"
            >
              Try Again
            </button>
          </div>
        ) : podcasts.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎙️</div>
            <h3 className="text-xl font-medium text-gray-900 dark:text-white mb-2">
              No podcasts yet
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              You haven't created any podcasts yet.
            </p>
            <Link
              to="/create"
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition"
            >
              Create Your First Podcast
            </Link>
          </div>
        ) : (
          <>
            {/* Dashboard stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
                <div className="text-3xl text-indigo-500 mb-2">🎧</div>
                <h3 className="text-xl font-medium text-gray-900 dark:text-white">
                  {podcasts.length}
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Total Podcasts
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
                <div className="text-3xl text-indigo-500 mb-2">⏱️</div>
                <h3 className="text-xl font-medium text-gray-900 dark:text-white">
                  {formatDuration(
                    podcasts.reduce((acc, podcast) => acc + podcast.duration, 0)
                  )}
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Total Duration
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
                <div className="text-3xl text-indigo-500 mb-2">📅</div>
                <h3 className="text-xl font-medium text-gray-900 dark:text-white">
                  {formatDate(podcasts[0].createdAt)}
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Latest Podcast
                </p>
              </div>
            </div>

            {/* Podcasts list */}
            <div className="grid grid-cols-1 gap-6">
              {podcasts.map((podcast) => (
                <motion.div
                  key={podcast.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className="podcast-card flex flex-col sm:flex-row bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden border border-gray-100 dark:border-gray-700"
                >
                  {/* Left part (album art / podcast type) */}
                  <div className="w-full sm:w-48 h-48 bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white">
                    <div className="text-7xl">
                      {getFormatIcon(podcast.format)}
                    </div>
                  </div>

                  {/* Right part (details) */}
                  <div className="flex-1 p-6 flex flex-col">
                    <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                      <div className="flex items-center mb-1">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-4 w-4 mr-1"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                        Created on {formatDate(podcast.createdAt)}
                      </div>
                      <div className="flex items-center">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-4 w-4 mr-1"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        {formatDuration(podcast.duration)}
                      </div>
                    </div>

                    <div className="mt-auto flex items-center justify-between">
                      <div className="flex items-center">
                        <button
                          onClick={() => togglePlayPause(podcast)}
                          className="podcast-control-btn"
                          aria-label={
                            currentlyPlaying === podcast.id ? "Pause" : "Play"
                          }
                        >
                          {currentlyPlaying === podcast.id ? (
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-6 w-6"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                              />
                            </svg>
                          ) : (
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-6 w-6"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                              />
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                              />
                            </svg>
                          )}
                        </button>

                        <a
                          href={podcast.audioUrl}
                          download
                          className="podcast-control-btn-sm ml-2 flex items-center justify-center"
                          aria-label="Download"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-5 w-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                            />
                          </svg>
                        </a>
                      </div>

                      <div className="text-sm font-medium text-indigo-600 dark:text-indigo-400 flex items-center">
                        <span className="mr-2">
                          {getFormatIcon(podcast.format)}
                        </span>
                        {podcast.format === "debate"
                          ? "Debate Style"
                          : podcast.format === "podcast"
                          ? "Podcast Style"
                          : "Duck Mode"}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
