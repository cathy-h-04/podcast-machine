// filepath: /Users/nicholas/Documents/GitHub/claude-yap/frontend/app/routes/profile.tsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { motion } from "framer-motion";

interface Prompt {
  id: string;
  title: string;
  content: string;
  createdAt: string;
}

export default function Profile() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [newPrompt, setNewPrompt] = useState({ title: "", content: "" });
  const [editingPromptId, setEditingPromptId] = useState<string | null>(null);
  const [user, setUser] = useState<{ name: string; email: string } | null>(
    null
  );

  const navigate = useNavigate();

  const handleLogout = () => {
    // Clear user data from localStorage
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("authToken");
    localStorage.removeItem("user");

    // Redirect to login page
    navigate("/login");
  };

  // Check if user is logged in
  useEffect(() => {
    const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";
    if (!isLoggedIn) {
      navigate("/login");
      return;
    }

    // Get user info
    const userInfo = localStorage.getItem("userInfo");
    if (userInfo) {
      setUser(JSON.parse(userInfo));
    }

    // Fetch user prompts
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("authToken");
      const response = await fetch("http://localhost:5111/api/prompts", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch prompts");
      }

      const data = await response.json();
      setPrompts(data.prompts || []);
    } catch (err) {
      setError("Failed to load your prompts. Please try again later.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setNewPrompt((prev) => ({ ...prev, [name]: value }));
  };

  const savePrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPrompt.title.trim() || !newPrompt.content.trim()) {
      setError("Please fill in both title and content fields");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const token = localStorage.getItem("authToken");
      const url = "http://localhost:5111/api/prompts";
      const method = editingPromptId ? "PUT" : "POST";
      const endpoint = editingPromptId ? `${url}/${editingPromptId}` : url;

      const response = await fetch(endpoint, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newPrompt),
      });

      if (!response.ok) {
        throw new Error("Failed to save prompt");
      }

      // Refresh prompts list
      await fetchPrompts();

      // Reset form
      setNewPrompt({ title: "", content: "" });
      setEditingPromptId(null);
    } catch (err) {
      setError("Failed to save your prompt. Please try again.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const startEditing = (prompt: Prompt) => {
    setNewPrompt({ title: prompt.title, content: prompt.content });
    setEditingPromptId(prompt.id);
  };

  const cancelEditing = () => {
    setNewPrompt({ title: "", content: "" });
    setEditingPromptId(null);
  };

  const deletePrompt = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this prompt?")) {
      return;
    }

    setIsLoading(true);
    try {
      const token = localStorage.getItem("authToken");
      const response = await fetch(`http://localhost:5111/api/prompts/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to delete prompt");
      }

      setPrompts((prevPrompts) =>
        prevPrompts.filter((prompt) => prompt.id !== id)
      );
    } catch (err) {
      setError("Failed to delete the prompt. Please try again.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="container mx-auto px-4 py-8 max-w-4xl"
    >
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-white">Your Profile</h1>
              {user && (
                <p className="text-indigo-100 mt-2">
                  {user.name} • {user.email}
                </p>
              )}
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-white text-indigo-600 rounded-md shadow hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        <div className="p-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
            Your Saved Prompts
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            Save prompts that you want Claude to remember about you. These will
            be available whenever you create a new project.
          </p>

          {error && (
            <div
              className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6"
              role="alert"
            >
              <p>{error}</p>
            </div>
          )}

          <form
            onSubmit={savePrompt}
            className="mb-8 bg-gray-50 dark:bg-gray-700 p-6 rounded-md"
          >
            <div className="mb-4">
              <label
                htmlFor="title"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Prompt Title
              </label>
              <input
                type="text"
                id="title"
                name="title"
                value={newPrompt.title}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-white"
                placeholder="e.g., Writing Style, Personal Details, Work Context"
                required
              />
            </div>

            <div className="mb-4">
              <label
                htmlFor="content"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Prompt Content
              </label>
              <textarea
                id="content"
                name="content"
                value={newPrompt.content}
                onChange={handleInputChange}
                rows={5}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:text-white"
                placeholder="What would you like Claude to remember about you? e.g., I prefer concise responses with examples, I work in healthcare and need HIPAA-compliant suggestions"
                required
              />
            </div>

            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md shadow focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {isLoading
                  ? "Saving..."
                  : editingPromptId
                  ? "Update Prompt"
                  : "Save Prompt"}
              </button>

              {editingPromptId && (
                <button
                  type="button"
                  onClick={cancelEditing}
                  className="px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-800 rounded-md shadow focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
              )}
            </div>
          </form>

          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-800 dark:text-white">
              {prompts.length === 0
                ? "You don't have any saved prompts yet"
                : "Your saved prompts"}
            </h3>

            {isLoading && prompts.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 dark:text-gray-400">
                  Loading your prompts...
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {prompts.map((prompt) => (
                  <div
                    key={prompt.id}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
                  >
                    <div className="flex justify-between items-start">
                      <h4 className="text-lg font-medium text-gray-900 dark:text-white">
                        {prompt.title}
                      </h4>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => startEditing(prompt)}
                          className="text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => deletePrompt(prompt.id)}
                          className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                    <p className="mt-2 text-gray-600 dark:text-gray-300 whitespace-pre-line">
                      {prompt.content}
                    </p>
                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                      Created: {new Date(prompt.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
