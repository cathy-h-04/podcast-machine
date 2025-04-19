import { useState, useEffect } from "react";

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
  const [prompt, setPrompt] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const [mode, setMode] = useState<"none" | "research" | "summaritive">("none");
  const [researchTopic, setResearchTopic] = useState("");
  const [podcastFormat, setPodcastFormat] = useState<
    "debate" | "podcast" | "duck" | "none"
  >("none");
  const [peopleCount, setPeopleCount] = useState<
    "one" | "two" | "three" | "none"
  >("none");

  // Form validation state
  const [promptTouched, setPromptTouched] = useState(false);
  const [researchTopicTouched, setResearchTopicTouched] = useState(false);

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

  const handlePeopleCountChange = (count: "one" | "two" | "three") => {
    setPeopleCount(count);
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
    setFiles((prevFiles) => [...prevFiles, ...pdfFiles]);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    // Only process dropped files if in summaritive mode
    if (mode === "summaritive") {
      const droppedFiles = Array.from(e.dataTransfer.files);
      const pdfFiles = droppedFiles.filter(
        (file) => file.type === "application/pdf"
      );
      setFiles((prevFiles) => [...prevFiles, ...pdfFiles]);
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

      fetch("http://localhost:5111/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          context: prompt,
          files: fileData, // Send the base64 encoded files
          mode,
          style: podcastFormat,
          num_people: peopleCount,
          content: researchTopic,
        }),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          return response.json();
        })
        .then((data) => {
          console.log("Response data:", data);
          // Handle the response data as needed
          // For example, you might want to redirect the user or show a success message
          // window.location.href = `/result/${data.id}`;
          // Or show a success message
          setIsLoading(false);
          alert("Podcast generated successfully!");
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("An error occurred while generating the podcast.");
        });
    } catch (error) {
      console.error("Error submitting request:", error);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-950 py-12 px-4">
      {/* Full-screen drag overlay */}
      {isDraggingFile && (
        <div
          className="fixed inset-0 bg-blue-500/30 backdrop-blur-sm z-50 flex items-center justify-center transition-all duration-300"
          onDragOver={handleDragOver}
          onDrop={(e) => {
            handleDrop(e);
            setIsDraggingFile(false);
          }}
        >
          <div className="bg-white dark:bg-gray-800 p-8 rounded-xl shadow-2xl text-center max-w-md mx-auto transform transition-transform duration-300 scale-110 border-2 border-blue-400 dark:border-blue-500">
            <div className="text-6xl mb-4">📄</div>
            <h3 className="text-xl font-bold mb-2 dark:text-white">
              Drop PDF Files Here
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Release to upload your PDF files
            </p>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
        <div className="bg-blue-600 dark:bg-blue-700 py-8 px-6 text-white">
          <h1 className="text-4xl font-bold text-center">Claude Yap</h1>
          <h2 className="text-xl mt-2 text-center text-blue-100">
            AI Podcast Generator
          </h2>
        </div>

        <div className="p-8">
          <div className="mb-8">
            <label
              htmlFor="prompt"
              className="block text-sm font-medium mb-2 dark:text-white"
            >
              Describe the style of the audio file that you would like to have
              generated <span className="text-red-500">*</span>
            </label>
            <textarea
              id="prompt"
              rows={5}
              className={`w-full p-4 border ${
                promptError
                  ? "border-red-500 dark:border-red-500"
                  : "border-gray-300 dark:border-gray-600"
              } rounded-lg shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50 transition-colors dark:bg-gray-700 dark:text-white`}
              placeholder="E.g., I would like to have a podcast between Joe Biden and Donald Trump..."
              value={prompt}
              onChange={handlePromptChange}
              onBlur={handlePromptBlur}
            />
            {promptError && (
              <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                Please describe the podcast you want to generate
              </p>
            )}
          </div>

          <div className="mb-8">
            <label className="block text-sm font-medium mb-2 dark:text-white">
              Choose a podcast format <span className="text-red-500">*</span>
            </label>
            <div className="flex flex-col sm:flex-row gap-4 mb-4">
              <button
                onClick={() => handlePodcastFormatChange("debate")}
                className={`flex-1 p-4 rounded-lg flex flex-col items-center transition-colors ${
                  podcastFormat === "debate"
                    ? "bg-blue-100 dark:bg-blue-900 border-2 border-blue-500"
                    : "bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:bg-blue-50 dark:hover:bg-gray-600"
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
                className={`flex-1 p-4 rounded-lg flex flex-col items-center transition-colors ${
                  podcastFormat === "podcast"
                    ? "bg-blue-100 dark:bg-blue-900 border-2 border-blue-500"
                    : "bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:bg-blue-50 dark:hover:bg-gray-600"
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
                className={`flex-1 p-4 rounded-lg flex flex-col items-center transition-colors ${
                  podcastFormat === "duck"
                    ? "bg-blue-100 dark:bg-blue-900 border-2 border-blue-500"
                    : "bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:bg-blue-50 dark:hover:bg-gray-600"
                }`}
              >
                <span className="text-3xl mb-2">🦆</span>
                <span className="font-medium dark:text-white">Duck Mode</span>
                <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                  Teacher answering student questions
                </span>
              </button>
            </div>
          </div>

          <div className="mb-8">
            <label className="block text-sm font-medium mb-2 dark:text-white">
              How many people should be in the audio?{" "}
              <span className="text-red-500">*</span>
            </label>
            <div className="flex flex-col sm:flex-row gap-4 mb-4">
              <button
                onClick={() => handlePeopleCountChange("one")}
                className={`flex-1 p-4 rounded-lg flex flex-col items-center transition-colors ${
                  peopleCount === "one"
                    ? "bg-blue-100 dark:bg-blue-900 border-2 border-blue-500"
                    : "bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:bg-blue-50 dark:hover:bg-gray-600"
                }`}
              >
                <span className="text-3xl mb-2">👤</span>
                <span className="font-medium dark:text-white">One Person</span>
                <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                  Solo monologue or narration
                </span>
              </button>

              <button
                onClick={() => handlePeopleCountChange("two")}
                className={`flex-1 p-4 rounded-lg flex flex-col items-center transition-colors ${
                  peopleCount === "two"
                    ? "bg-blue-100 dark:bg-blue-900 border-2 border-blue-500"
                    : "bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:bg-blue-50 dark:hover:bg-gray-600"
                }`}
              >
                <span className="text-3xl mb-2">👤👤</span>
                <span className="font-medium dark:text-white">Two People</span>
                <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                  Dialogue between two individuals
                </span>
              </button>

              <button
                onClick={() => handlePeopleCountChange("three")}
                className={`flex-1 p-4 rounded-lg flex flex-col items-center transition-colors ${
                  peopleCount === "three"
                    ? "bg-blue-100 dark:bg-blue-900 border-2 border-blue-500"
                    : "bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:bg-blue-50 dark:hover:bg-gray-600"
                }`}
              >
                <span className="text-3xl mb-2">👤👤👤</span>
                <span className="font-medium dark:text-white">
                  Three People
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                  Group discussion or panel
                </span>
              </button>
            </div>
          </div>

          <div className="mb-8">
            <label className="block text-sm font-medium mb-2 dark:text-white">
              Choose how Claude should create the podcast content{" "}
              <span className="text-red-500">*</span>
            </label>
            <div className="flex flex-col sm:flex-row gap-4 mb-4">
              <button
                onClick={() => handleModeChange("research")}
                className={`flex-1 p-4 rounded-lg flex flex-col items-center transition-colors ${
                  mode === "research"
                    ? "bg-blue-100 dark:bg-blue-900 border-2 border-blue-500"
                    : "bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:bg-blue-50 dark:hover:bg-gray-600"
                }`}
              >
                <span className="text-3xl mb-2">🔍</span>
                <span className="font-medium dark:text-white">AI Research</span>
                <span className="text-sm text-gray-500 dark:text-gray-400 mt-1 text-center">
                  Claude will research your topic
                </span>
              </button>

              <button
                onClick={() => handleModeChange("summaritive")}
                className={`flex-1 p-4 rounded-lg flex flex-col items-center transition-colors ${
                  mode === "summaritive"
                    ? "bg-blue-100 dark:bg-blue-900 border-2 border-blue-500"
                    : "bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:bg-blue-50 dark:hover:bg-gray-600"
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
          </div>

          {mode === "research" && (
            <div className="mb-8">
              <label
                htmlFor="research-topic"
                className="block text-sm font-medium mb-2 dark:text-white"
              >
                Describe the content you want Claude to research{" "}
                <span className="text-red-500">*</span>
              </label>
              <textarea
                id="research-topic"
                rows={4}
                className={`w-full p-4 border ${
                  researchTopicError
                    ? "border-red-500 dark:border-red-500"
                    : "border-gray-300 dark:border-gray-600"
                } rounded-lg shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50 transition-colors dark:bg-gray-700 dark:text-white`}
                placeholder="E.g., Research the latest developments in quantum computing, focusing on quantum error correction..."
                value={researchTopic}
                onChange={handleResearchTopicChange}
                onBlur={handleResearchTopicBlur}
              />
              {researchTopicError && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                  Please describe what you want Claude to research
                </p>
              )}
            </div>
          )}

          {mode === "summaritive" && (
            <div className="mb-8">
              <label className="block text-sm font-medium mb-2 dark:text-white">
                Upload PDF files to summarize{" "}
                <span className="text-red-500">*</span>
              </label>
              <div
                className="border-dashed border-2 border-blue-300 dark:border-blue-500 rounded-lg p-8 text-center bg-blue-50 dark:bg-gray-700/50 hover:bg-blue-100 dark:hover:bg-gray-700 transition-colors"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
              >
                <div className="text-4xl mb-3">📄</div>
                <input
                  type="file"
                  accept=".pdf"
                  multiple
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium"
                >
                  Click to upload PDFs or drag and drop here
                </label>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  PDF files only
                </p>
              </div>

              {files.length > 0 && (
                <div className="mt-6 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <h3 className="text-sm font-medium mb-3 dark:text-white">
                    Uploaded files:
                  </h3>
                  <ul className="space-y-2">
                    {files.map((file, index) => (
                      <li
                        key={index}
                        className="flex justify-between items-center p-3 bg-white dark:bg-gray-700 rounded-lg shadow-sm"
                      >
                        <div className="flex items-center">
                          <span className="text-lg mr-2">📄</span>
                          <span className="text-black dark:text-white font-medium">
                            {file.name}
                          </span>
                        </div>
                        <button
                          onClick={() => removeFile(index)}
                          className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 p-1.5 rounded-full hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors"
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
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="text-center">
            <button
              onClick={handleSubmit}
              disabled={
                isLoading ||
                prompt.trim().length === 0 ||
                mode === "none" ||
                podcastFormat === "none" ||
                peopleCount === "none" ||
                (mode === "research" && researchTopic.trim().length === 0) ||
                (mode === "summaritive" && files.length === 0)
              }
              className={`px-8 py-3 rounded-full font-medium text-lg shadow-lg transform transition-all duration-200 ${
                isLoading ||
                prompt.trim().length === 0 ||
                mode === "none" ||
                podcastFormat === "none" ||
                peopleCount === "none" ||
                (mode === "research" && researchTopic.trim().length === 0) ||
                (mode === "summaritive" && files.length === 0)
                  ? "bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 text-white hover:shadow-xl active:scale-95"
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
                  Generating...
                </span>
              ) : (
                "Generate Podcast"
              )}
            </button>
            <p className="mt-4 text-xs text-gray-500 dark:text-gray-400">
              Powered by Claude AI
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
