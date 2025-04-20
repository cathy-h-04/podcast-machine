import { useState, useEffect, useRef } from "react";
// Note: We're using motion components for animations
// If framer-motion is not installed, you'll need to run: npm install framer-motion
import { motion } from "framer-motion";

export function meta({}) {
  return [
    { title: "Claude Yap - AI Podcast Generator" },
    {
      name: "description",
      content: "Create AI-generated podcasts with Claude",
    },
  ];
}

export default function Home() {
  // Main form state
  const [prompt, setPrompt] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const [mode, setMode] = useState<"none" | "research" | "summaritive">("none");
  const [researchTopic, setResearchTopic] = useState("");
  const [podcastFormat, setPodcastFormat] = useState<
    "debate" | "podcast" | "duck" | "none"
  >("none");
  
  // Progress tracking state
  const [currentPodcastId, setCurrentPodcastId] = useState<string | null>(null);
  const [progressStatus, setProgressStatus] = useState<{
    status: string;
    step: string;
    progress: number;
    message: string;
  } | null>(null);
  const [progressPollingActive, setProgressPollingActive] = useState(false);

  // Form validation state
  const [promptTouched, setPromptTouched] = useState(false);
  const [researchTopicTouched, setResearchTopicTouched] = useState(false);

  // Refs for file input and drag area
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragAreaRef = useRef<HTMLDivElement>(null);

  // Animation states
  const [isFormVisible, setIsFormVisible] = useState(true);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  // Validation errors
  const promptError = promptTouched && prompt.trim().length === 0;
  const researchTopicError =
    researchTopicTouched &&
    researchTopic.trim().length === 0 &&
    mode === "research";

  useEffect(() => {
    const handleDocumentDragEnter = (e: DragEvent) => {
      e.preventDefault();
      // Only show drag overlay if in summarize mode
      if (e.dataTransfer?.types.includes("Files") && mode === "summaritive") {
        setIsDraggingFile(true);
      }
    };

    const handleDocumentDragLeave = (e: DragEvent) => {
      e.preventDefault();
      // Only consider it a leave if we're leaving the document
      if (e.relatedTarget === null) {
        setIsDraggingFile(false);
      }
    };

    const handleDocumentDragOver = (e: DragEvent) => {
      e.preventDefault();
    };

    const handleDocumentDrop = (e: DragEvent) => {
      e.preventDefault();
      setIsDraggingFile(false);
    };

    document.addEventListener("dragenter", handleDocumentDragEnter);
    document.addEventListener("dragleave", handleDocumentDragLeave);
    document.addEventListener("dragover", handleDocumentDragOver);
    document.addEventListener("drop", handleDocumentDrop);

    return () => {
      document.removeEventListener("dragenter", handleDocumentDragEnter);
      document.removeEventListener("dragleave", handleDocumentDragLeave);
      document.removeEventListener("dragover", handleDocumentDragOver);
      document.removeEventListener("drop", handleDocumentDrop);
    };
  }, [mode]); // Add mode as a dependency

  const handlePromptChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
  };

  const handlePromptBlur = () => {
    setPromptTouched(true);
  };

  const handleResearchTopicChange = (
    e: React.ChangeEvent<HTMLTextAreaElement>
  ) => {
    setResearchTopic(e.target.value);
  };

  const handleResearchTopicBlur = () => {
    setResearchTopicTouched(true);
  };

  const handlePodcastFormatChange = (
    selectedFormat: "debate" | "podcast" | "duck"
  ) => {
    setPodcastFormat(selectedFormat);
  };

  const handleModeChange = (selectedMode: "research" | "summaritive") => {
    setMode(selectedMode);
    // Reset files when switching to research mode
    if (selectedMode === "research") {
      setFiles([]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    const pdfFiles = selectedFiles.filter(
      (file) => file.type === "application/pdf"
    );

    // Limit to 2 PDF files in total
    if (files.length + pdfFiles.length <= 2) {
      setFiles((prevFiles) => [...prevFiles, ...pdfFiles]);
    } else {
      // If user tries to add more than 2 files, only add enough to reach the limit
      const availableSlots = Math.max(0, 2 - files.length);
      if (availableSlots > 0) {
        setFiles((prevFiles) => [
          ...prevFiles,
          ...pdfFiles.slice(0, availableSlots),
        ]);
      }

      // Show alert about file limit
      alert(
        "Maximum of 2 PDF files allowed. Only the first 2 files will be used."
      );
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    // Only process dropped files if in summaritive mode
    if (mode === "summaritive") {
      const droppedFiles = Array.from(e.dataTransfer.files);
      const pdfFiles = droppedFiles.filter(
        (file) => file.type === "application/pdf"
      );

      // Limit to 2 PDF files in total
      if (files.length + pdfFiles.length <= 2) {
        setFiles((prevFiles) => [...prevFiles, ...pdfFiles]);
      } else {
        // If user tries to drop more than 2 files, only add enough to reach the limit
        const availableSlots = Math.max(0, 2 - files.length);
        if (availableSlots > 0) {
          setFiles((prevFiles) => [
            ...prevFiles,
            ...pdfFiles.slice(0, availableSlots),
          ]);
        }

        // Show alert about file limit
        alert(
          "Maximum of 2 PDF files allowed. Only the first 2 files will be used."
        );
      }
    }
    setIsDraggingFile(false);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setProgressStatus(null);
    setCurrentPodcastId(null);

    // Hide the form with animation
    setIsFormVisible(false);

    try {
      // First, convert any files to base64 format
      const filePromises = files.map((file) => {
        return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            // The result will be a base64 string
            const base64String = reader.result as string;
            // Extract the base64 data without the prefix
            const base64Data = base64String.split(",")[1];
            resolve(base64Data);
          };
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
      });

      // Wait for all files to be converted to base64
      const fileData = await Promise.all(filePromises);

      // Create request data
      const requestData = {
        context: prompt,
        files: fileData,
        mode,
        style: podcastFormat,
        content: researchTopic,
      };

      // Send the request
      const token = localStorage.getItem("authToken");
      const response = await fetch("http://localhost:5111/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(
          `Server responded with ${response.status}: ${response.statusText}`
        );
      }

      const data = await response.json();
      console.log("Response data:", data);

      // If we have a podcast_id from the script generation, generate audio and cover art for it
      if (data.podcast_id) {
        try {
          console.log("Generating audio for podcast ID:", data.podcast_id);

          // Set the current podcast ID for progress tracking
          setCurrentPodcastId(data.podcast_id);

          // Start polling for progress updates
          setProgressPollingActive(true);

          // Initial progress status
          setProgressStatus({
            status: "initializing",
            step: "setup",
            progress: 5,
            message: "Preparing to generate audio...",
          });

          // Call the audio generation endpoint
          const audioResponse = await fetch(
            "http://localhost:5111/api/generate-audio",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                podcast_id: data.podcast_id,
                script: data.script,
              }),
            }
          );

          if (!audioResponse.ok) {
            console.error("Error generating audio:", audioResponse.statusText);
            setProgressStatus({
              status: "error",
              step: "audio_generation",
              progress: 0,
              message: `Error: ${audioResponse.statusText}`,
            });
          } else {
            const audioData = await audioResponse.json();
            console.log("Audio generated successfully:", audioData);

            // Wait for the progress polling to show 100% before continuing
            // This ensures our UI shows the complete progress
            let attempts = 0;
            while (progressStatus?.progress !== 100 && attempts < 10) {
              await new Promise((resolve) => setTimeout(resolve, 500));
              attempts++;
            }
          }
        } catch (audioError) {
          console.error("Error generating audio:", audioError);
          // Continue with success message even if audio generation fails
        }

        // Generate cover art
        try {
          console.log("Generating cover art for podcast ID:", data.podcast_id);

          // Create a prompt for the cover art based on the podcast title and style
          const coverPrompt = `Create a podcast cover art for "${data.settings_used.title}". Style: ${data.style}.`;

          // Call the cover art generation endpoint
          const coverResponse = await fetch(
            "http://localhost:5111/api/generate-cover",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                podcast_id: data.podcast_id,
                prompt: coverPrompt,
              }),
            }
          );

          if (!coverResponse.ok) {
            console.error("Error generating cover art:", coverResponse.statusText);
          } else {
            const coverData = await coverResponse.json();
            console.log("Cover art generated successfully:", coverData);
          }
        } catch (coverError) {
          console.error("Error generating cover art:", coverError);
          // Continue with success message even if cover art generation fails
        }
      }

      // Show success message
      setShowSuccessMessage(true);

      // Stop progress polling
      setProgressPollingActive(false);

      // Reset form after a delay
      setTimeout(() => {
        setIsLoading(false);
        setIsFormVisible(true);
        setShowSuccessMessage(false);
        setProgressStatus(null);
        setCurrentPodcastId(null);
      }, 3000);

      alert("Podcast generated successfully!");
    } catch (error) {
      console.error("Error submitting request:", error);
      alert(
        `An error occurred: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
      setIsLoading(false);
      setIsFormVisible(true);
      setProgressPollingActive(false);
      setProgressStatus({
        status: "error",
        step: "submission",
        progress: 0,
        message: error instanceof Error ? error.message : String(error),
      });
    }
  };

  // Effect for polling progress updates
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const pollProgress = async () => {
      if (!progressPollingActive || !currentPodcastId) return;

      try {
        const token = localStorage.getItem("authToken");
        const response = await fetch(
          `http://localhost:5111/api/audio-progress/${currentPodcastId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.ok) {
          const progressData = await response.json();
          setProgressStatus(progressData);

          // If we're done or there's an error, stop polling
          if (progressData.status === "complete" || progressData.status === "error") {
            setProgressPollingActive(false);
          }
        } else {
          console.error("Error fetching progress:", response.statusText);
        }
      } catch (error) {
        console.error("Error polling progress:", error);
      }
    };

    if (progressPollingActive && currentPodcastId) {
      // Poll immediately
      pollProgress();
      // Then set up interval
      intervalId = setInterval(pollProgress, 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [progressPollingActive, currentPodcastId]);

  return (
    <div className="min-h-screen py-6 px-4 sm:px-6 bg-gradient-to-b from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-950">
      {/* Success message */}
      {showSuccessMessage && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          className="fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-70"
        >
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-8 rounded-lg shadow-2xl max-w-md w-full border border-indigo-500">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-6">
                <svg
                  className="h-10 w-10 text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M5 13l4 4L19 7"
                  ></path>
                </svg>
              </div>
              <h3 className="text-2xl leading-6 font-medium text-indigo-300 mb-2">
                Success!
              </h3>
              <p className="text-gray-300 mb-6">
                Your podcast has been generated successfully. You can find it in
                your dashboard.
              </p>
              <a
                href="/dashboard"
                className="inline-flex items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Go to Dashboard
              </a>
            </div>
          </div>
        </motion.div>
      )}

      {/* Progress bar overlay */}
      {isLoading && progressStatus && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 flex flex-col items-center justify-center z-40 bg-black bg-opacity-70"
        >
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-8 rounded-lg shadow-2xl max-w-md w-full border border-indigo-500">
            <h3 className="text-xl leading-6 font-medium text-indigo-300 mb-4">
              Generating Your Podcast
            </h3>

            <div className="mb-4">
              <div className="relative pt-1">
                <div className="flex mb-2 items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-indigo-200 bg-indigo-900">
                      {progressStatus.step.replace("_", " ").toUpperCase()}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold inline-block text-indigo-200">
                      {progressStatus.progress}%
                    </span>
                  </div>
                </div>
                <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-indigo-900">
                  <div
                    style={{ width: `${progressStatus.progress}%` }}
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-indigo-500 transition-all duration-500 ease-in-out"
                  ></div>
                </div>
              </div>
            </div>

            <p className="text-gray-300 mb-2 text-center">
              {progressStatus.message}
            </p>

            {progressStatus.status === "error" && (
              <div className="mt-4 p-3 bg-red-900 bg-opacity-50 border border-red-700 rounded-md">
                <p className="text-red-300 text-sm">
                  An error occurred. We'll still try to generate a podcast with
                  what we have.
                </p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Full-screen drag overlay */}
      {isDraggingFile && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-indigo-500/30 backdrop-blur-sm z-50 flex items-center justify-center transition-all duration-300"
          onDragOver={handleDragOver}
          onDrop={(e) => {
            handleDrop(e);
            setIsDraggingFile(false);
          }}
          ref={dragAreaRef}
        >
          <motion.div
            initial={{ scale: 0.9, y: 10 }}
            animate={{ scale: 1, y: 0 }}
            transition={{
              type: "spring",
              damping: 15,
              repeat: Infinity,
              repeatType: "reverse",
              duration: 1.5,
            }}
            className="glass-effect p-8 text-center max-w-md mx-auto border-2 border-indigo-400 dark:border-indigo-500 rounded-xl shadow-lg"
          >
            <div className="text-6xl mb-4 animate-pulse-slow">📄</div>
            <h3 className="text-xl font-bold mb-2 dark:text-white">
              Drop PDF Files Here
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Release to upload your PDF files
            </p>
          </motion.div>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-4xl mx-auto podcast-card overflow-visible"
      >
        <div className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-600 dark:from-indigo-700 dark:via-violet-700 dark:to-indigo-600 py-10 px-6 text-white rounded-t-xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full opacity-10">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 1440 320"
              className="absolute bottom-0 left-0"
            >
              <path
                fill="rgba(255,255,255,0.3)"
                fillOpacity="1"
                d="M0,192L48,176C96,160,192,128,288,122.7C384,117,480,139,576,165.3C672,192,768,224,864,213.3C960,203,1056,149,1152,133.3C1248,117,1344,139,1392,149.3L1440,160L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
              ></path>
            </svg>
          </div>
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", damping: 10 }}
            className="flex items-center justify-center mb-6 relative z-10"
          >
            <div className="bg-white/20 p-4 rounded-full mr-4 shadow-lg">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-12 w-12"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13v8l6-4z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl sm:text-5xl font-bold tracking-tight">
                Claude Yap
              </h1>
              <div className="h-1 w-20 bg-white/50 rounded-full mt-1"></div>
            </div>
          </motion.div>
          <h2 className="text-lg sm:text-2xl text-center text-indigo-100 font-light relative z-10">
            AI Podcast Generator
          </h2>
        </div>

        <div className="p-6 sm:p-8 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-b-xl">
          <div className="mb-8">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.4 }}
            >
              <label htmlFor="prompt" className="form-label flex items-center">
                <span className="mr-2">🎧</span>
                Describe the style of the audio file that you would like to have
                generated <span className="text-red-500 ml-1">*</span>
              </label>
              <textarea
                id="prompt"
                rows={5}
                className={`form-input ${
                  promptError ? "ring-red-500 dark:ring-red-500" : ""
                }`}
                placeholder="E.g., I would like to have a podcast between Joe Biden and Donald Trump..."
                value={prompt}
                onChange={handlePromptChange}
                onBlur={handlePromptBlur}
              />
              {promptError && (
                <motion.p
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4 mr-1"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Please describe the podcast you want to generate
                </motion.p>
              )}
            </motion.div>
          </div>

          <div className="mb-8">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.4 }}
            >
              <label className="form-label flex items-center">
                <span className="mr-2">🎭</span>
                Choose a podcast format{" "}
                <span className="text-red-500 ml-1">*</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                <button
                  onClick={() => handlePodcastFormatChange("debate")}
                  className={`option-card flex flex-col items-center ${
                    podcastFormat === "debate" ? "selected" : ""
                  }`}
                >
                  <span className="text-3xl mb-2">🎭</span>
                  <span className="font-medium dark:text-white">
                    Debate Style
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                    Two perspectives debating a topic
                  </span>
                </button>

                <button
                  onClick={() => handlePodcastFormatChange("podcast")}
                  className={`option-card flex flex-col items-center ${
                    podcastFormat === "podcast" ? "selected" : ""
                  }`}
                >
                  <span className="text-3xl mb-2">🎙️</span>
                  <span className="font-medium dark:text-white">
                    Podcast Style
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                    Conversational discussion format
                  </span>
                </button>

                <button
                  onClick={() => handlePodcastFormatChange("duck")}
                  className={`option-card flex flex-col items-center ${
                    podcastFormat === "duck" ? "selected" : ""
                  }`}
                >
                  <span className="text-3xl mb-2">🦆</span>
                  <span className="font-medium dark:text-white">Duck Mode</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                    Teacher answering student questions
                  </span>
                </button>
              </div>
            </motion.div>
          </div>

          <div className="mb-8">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.4 }}
            >
              <label className="form-label flex items-center">
                <span className="mr-2">🤖</span>
                Choose how Claude should create the podcast content{" "}
                <span className="text-red-500 ml-1">*</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-4">
                <button
                  onClick={() => handleModeChange("research")}
                  className={`option-card flex flex-col items-center ${
                    mode === "research" ? "selected" : ""
                  }`}
                >
                  <span className="text-3xl mb-2">🔍</span>
                  <span className="font-medium dark:text-white">
                    AI Research
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                    Claude will research your topic
                  </span>
                </button>

                <button
                  onClick={() => handleModeChange("summaritive")}
                  className={`option-card flex flex-col items-center ${
                    mode === "summaritive" ? "selected" : ""
                  }`}
                >
                  <span className="text-3xl mb-2">📄</span>
                  <span className="font-medium dark:text-white">
                    File Summary
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                    Claude will summarize your files
                  </span>
                </button>
              </div>
            </motion.div>
          </div>

          {mode === "research" && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mb-8 overflow-hidden"
            >
              <div className="border-l-4 border-indigo-400 dark:border-indigo-600 pl-4 py-1">
                <label
                  htmlFor="research-topic"
                  className="form-label flex items-center"
                >
                  <span className="mr-2">🔍</span>
                  Describe the content you want Claude to research{" "}
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <textarea
                  id="research-topic"
                  rows={4}
                  className={`form-input ${
                    researchTopicError ? "ring-red-500 dark:ring-red-500" : ""
                  }`}
                  placeholder="E.g., Research the latest developments in quantum computing, focusing on quantum error correction..."
                  value={researchTopic}
                  onChange={handleResearchTopicChange}
                  onBlur={handleResearchTopicBlur}
                />
                {researchTopicError && (
                  <motion.p
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4 mr-1"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Please describe what you want Claude to research
                  </motion.p>
                )}
              </div>
            </motion.div>
          )}

          {mode === "summaritive" && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mb-8 overflow-hidden"
            >
              <div className="border-l-4 border-indigo-400 dark:border-indigo-600 pl-4 py-1">
                <label className="form-label flex items-center">
                  <span className="mr-2">📄</span>
                  Upload PDF files to summarize{" "}
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <div
                  className="border-dashed border-2 border-indigo-300 dark:border-indigo-500 rounded-lg p-8 text-center bg-indigo-50/80 dark:bg-gray-700/50 hover:bg-indigo-100/80 dark:hover:bg-gray-700 transition-all duration-300 transform hover:scale-[1.01] cursor-pointer shadow-sm hover:shadow-md"
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="text-5xl mb-3 animate-pulse-slow">📄</div>
                  <input
                    type="file"
                    accept=".pdf"
                    multiple
                    onChange={handleFileChange}
                    className="hidden"
                    ref={fileInputRef}
                  />
                  <div className="cursor-pointer text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium">
                    Click to upload PDFs or drag and drop here
                  </div>
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    PDF files only (Maximum 2 files)
                  </p>
                  <div className="mt-3 flex items-center justify-center text-sm">
                    <span
                      className={`font-medium ${
                        files.length >= 2 ? "text-red-500" : "text-indigo-500"
                      }`}
                    >
                      {files.length}/2 files uploaded
                    </span>
                  </div>
                </div>

                {files.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-6 glass-effect rounded-lg p-4 border border-indigo-100 dark:border-indigo-800/30"
                  >
                    <h3 className="text-sm font-medium mb-3 dark:text-white flex items-center">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-4 w-4 mr-1 text-indigo-500"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
                      </svg>
                      Uploaded files:
                    </h3>
                    <ul className="space-y-2">
                      {files.map((file, index) => (
                        <motion.li
                          key={index}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 10 }}
                          transition={{ duration: 0.2 }}
                          className="flex justify-between items-center p-3 bg-white/80 dark:bg-gray-700/80 rounded-lg shadow-sm border border-gray-100 dark:border-gray-600/30 hover:shadow-md transition-all duration-200"
                        >
                          <div className="flex items-center">
                            <span className="text-lg mr-2">📄</span>
                            <span className="text-black dark:text-white font-medium">
                              {file.name}
                            </span>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeFile(index);
                            }}
                            className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 p-1.5 rounded-full hover:bg-red-50 dark:hover:bg-red-900/30 transition-all duration-200 transform hover:scale-110"
                            title="Remove file"
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-5 w-5"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                            >
                              <path
                                fillRule="evenodd"
                                d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </button>
                        </motion.li>
                      ))}
                    </ul>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
            className="text-center mt-12"
          >
            <div className="relative inline-block">
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full blur opacity-30 group-hover:opacity-100 transition duration-1000 group-hover:duration-200"></div>
              <button
                onClick={handleSubmit}
                disabled={
                  isLoading ||
                  prompt.trim().length === 0 ||
                  mode === "none" ||
                  podcastFormat === "none" ||
                  (mode === "research" && researchTopic.trim().length === 0) ||
                  (mode === "summaritive" && files.length === 0)
                }
                className={`btn-primary relative ${
                  isLoading ||
                  prompt.trim().length === 0 ||
                  mode === "none" ||
                  podcastFormat === "none" ||
                  (mode === "research" && researchTopic.trim().length === 0) ||
                  (mode === "summaritive" && files.length === 0)
                    ? "btn-disabled"
                    : ""
                }`}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    {progressStatus ? progressStatus.message : "Generating..."}
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 mr-2"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Generate Podcast
                  </span>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
