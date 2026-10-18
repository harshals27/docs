import {
  useEffect,
  useRef,
  useState
} from "react";

import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  Prism as SyntaxHighlighter
} from "react-syntax-highlighter";

import {
  oneDark
} from "react-syntax-highlighter/dist/esm/styles/prism";

import "./App.css";


const STORAGE_KEY = "chat_sessions";
const API_BASE_URL = "http://127.0.0.1:8000";

const ALLOWED_FILE_EXTENSIONS = [
  ".pdf",
  ".docx",
  ".txt",
  ".csv"
];

const MAX_FILE_SIZE_MB = 25;
const MAX_FILE_SIZE_BYTES =
  MAX_FILE_SIZE_MB * 1024 * 1024;


const generateId = () =>
  `msg_${Date.now()}_${Math.random()
    .toString(36)
    .slice(2)}`;


const generateSessionId = () =>
  `session_${Date.now()}_${Math.random()
    .toString(36)
    .slice(2)}`;


const generateTemporaryAttachmentId = () =>
  `temp_${Date.now()}_${Math.random()
    .toString(36)
    .slice(2)}`;


const getTimestamp = () =>
  new Date().toISOString();


const createEmptySession = () => ({
  sessionId: generateSessionId(),
  title: "New Chat",
  messages: [],
  attachments: []
});


const getFileExtension = filename => {
  const dotIndex = filename.lastIndexOf(".");

  if (dotIndex === -1) {
    return "";
  }

  return filename
    .slice(dotIndex)
    .toLowerCase();
};


const formatFileSize = bytes => {
  if (!bytes) {
    return "0 KB";
  }

  if (bytes < 1024 * 1024) {
    return `${Math.ceil(bytes / 1024)} KB`;
  }

  return `${(
    bytes /
    (1024 * 1024)
  ).toFixed(1)} MB`;
};


function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] =
    useState(false);
  const [uploading, setUploading] =
    useState(false);
  const [uploadError, setUploadError] =
    useState("");
  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const [
    openMenuSessionId,
    setOpenMenuSessionId
  ] = useState(null);

  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);

  const [sessions, setSessions] = useState(
    () => {
      try {
        const saved =
          localStorage.getItem(STORAGE_KEY);

        if (saved) {
          const parsed = JSON.parse(saved);

          if (
            Array.isArray(parsed.sessions) &&
            parsed.sessions.length > 0
          ) {
            return {
              activeSessionId:
                parsed.activeSessionId,
              sessions: parsed.sessions.map(
                session => ({
                  ...session,
                  messages:
                    session.messages || [],
                  attachments:
                    session.attachments || []
                })
              )
            };
          }
        }
      } catch (error) {
        console.error(
          "Unable to restore sessions:",
          error
        );
      }

      const defaultSession =
        createEmptySession();

      return {
        activeSessionId:
          defaultSession.sessionId,
        sessions: [defaultSession]
      };
    }
  );


  const activeSession =
    sessions.sessions.find(
      session =>
        session.sessionId ===
        sessions.activeSessionId
    ) || sessions.sessions[0];


  const messages =
    activeSession?.messages || [];


  const attachments =
    activeSession?.attachments || [];


  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(sessions)
    );
  }, [sessions]);


  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth"
    });
  }, [messages, attachments]);


  const updateSession = (
    sessionId,
    updater
  ) => {
    setSessions(previous => ({
      ...previous,
      sessions: previous.sessions.map(
        session =>
          session.sessionId === sessionId
            ? updater(session)
            : session
      )
    }));
  };


  const createNewChat = () => {
    const newSession = createEmptySession();

    setSessions(previous => ({
      activeSessionId:
        newSession.sessionId,
      sessions: [
        newSession,
        ...previous.sessions
      ]
    }));

    setQuery("");
    setUploadError("");
    setOpenMenuSessionId(null);

    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };


  const switchSession = sessionId => {
    setSessions(previous => ({
      ...previous,
      activeSessionId: sessionId
    }));

    setQuery("");
    setUploadError("");
    setOpenMenuSessionId(null);

    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };


  const renameSession = sessionId => {
    const session =
      sessions.sessions.find(
        item =>
          item.sessionId === sessionId
      );

    const newTitle = window.prompt(
      "Enter new chat title",
      session?.title || ""
    );

    if (!newTitle?.trim()) {
      return;
    }

    updateSession(
      sessionId,
      currentSession => ({
        ...currentSession,
        title: newTitle.trim()
      })
    );

    setOpenMenuSessionId(null);
  };


  const deleteAttachmentFromServer =
    async attachmentId => {
      if (!attachmentId) {
        return;
      }

      await axios.delete(
        `${API_BASE_URL}/attachments/${attachmentId}`
      );
    };


  const deleteSession = async sessionId => {
    const confirmed = window.confirm(
      "Delete this chat session?"
    );

    if (!confirmed) {
      return;
    }

    const sessionToDelete =
      sessions.sessions.find(
        session =>
          session.sessionId === sessionId
      );

    const indexedAttachments =
      (
        sessionToDelete?.attachments || []
      ).filter(
        attachment =>
          attachment.status === "ready" &&
          attachment.attachmentId
      );

    await Promise.allSettled(
      indexedAttachments.map(attachment =>
        deleteAttachmentFromServer(
          attachment.attachmentId
        )
      )
    );

    setSessions(previous => {
      const remainingSessions =
        previous.sessions.filter(
          session =>
            session.sessionId !== sessionId
        );

      if (remainingSessions.length === 0) {
        const newSession =
          createEmptySession();

        return {
          activeSessionId:
            newSession.sessionId,
          sessions: [newSession]
        };
      }

      const nextActiveSessionId =
        previous.activeSessionId ===
        sessionId
          ? remainingSessions[0].sessionId
          : previous.activeSessionId;

      return {
        activeSessionId:
          nextActiveSessionId,
        sessions: remainingSessions
      };
    });

    setOpenMenuSessionId(null);
  };


  const validateFile = file => {
    const extension =
      getFileExtension(file.name);

    if (
      !ALLOWED_FILE_EXTENSIONS.includes(
        extension
      )
    ) {
      return (
        `${file.name} is not supported. ` +
        "Choose a PDF, DOCX, TXT, or CSV file."
      );
    }

    if (file.size === 0) {
      return `${file.name} is empty.`;
    }

    if (
      file.size > MAX_FILE_SIZE_BYTES
    ) {
      return (
        `${file.name} exceeds the ` +
        `${MAX_FILE_SIZE_MB} MB limit.`
      );
    }

    return null;
  };


  const updateAttachment = (
    sessionId,
    localId,
    changes
  ) => {
    updateSession(
      sessionId,
      currentSession => ({
        ...currentSession,
        attachments: (
          currentSession.attachments || []
        ).map(attachment =>
          attachment.localId === localId
            ? {
                ...attachment,
                ...changes
              }
            : attachment
        )
      })
    );
  };


  const uploadSingleFile = async (
    file,
    sessionId
  ) => {
    const localId =
      generateTemporaryAttachmentId();

    const temporaryAttachment = {
      localId,
      attachmentId: null,
      filename: file.name,
      size: file.size,
      status: "uploading",
      error: ""
    };

    updateSession(
      sessionId,
      currentSession => ({
        ...currentSession,
        attachments: [
          ...(currentSession.attachments ||
            []),
          temporaryAttachment
        ]
      })
    );

    const formData = new FormData();

    formData.append(
      "session_id",
      sessionId
    );

    formData.append("file", file);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/attachments/upload`,
        formData
      );

      const uploadedAttachment =
        response.data?.attachment;

      if (
        !uploadedAttachment?.attachment_id
      ) {
        throw new Error(
          "The upload response did not contain an attachment ID."
        );
      }

      updateAttachment(
        sessionId,
        localId,
        {
          attachmentId:
            uploadedAttachment.attachment_id,
          filename:
            uploadedAttachment.filename ||
            file.name,
          chunkCount:
            uploadedAttachment.chunk_count ||
            0,
          status: "ready",
          error: ""
        }
      );
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.error ||
        error.message ||
        "Attachment upload failed.";

      updateAttachment(
        sessionId,
        localId,
        {
          status: "failed",
          error: message
        }
      );
    }
  };


  const handleFileSelection = async event => {
    const files = Array.from(
      event.target.files || []
    );

    event.target.value = "";

    if (
      files.length === 0 ||
      uploading
    ) {
      return;
    }

    const validFiles = [];
    const errors = [];

    files.forEach(file => {
      const error = validateFile(file);

      if (error) {
        errors.push(error);
      } else {
        validFiles.push(file);
      }
    });

    setUploadError(errors.join(" "));

    if (validFiles.length === 0) {
      return;
    }

    const sessionId =
      sessions.activeSessionId;

    setUploading(true);

    try {
      for (const file of validFiles) {
        await uploadSingleFile(
          file,
          sessionId
        );
      }
    } finally {
      setUploading(false);
    }
  };


  const openFilePicker = () => {
    if (loading || uploading) {
      return;
    }

    fileInputRef.current?.click();
  };


  const removeAttachment =
    async attachment => {
      if (
        attachment.status === "uploading"
      ) {
        return;
      }

      setUploadError("");

      if (
        attachment.status === "ready" &&
        attachment.attachmentId
      ) {
        try {
          await deleteAttachmentFromServer(
            attachment.attachmentId
          );
        } catch (error) {
          setUploadError(
            error.response?.data?.detail ||
              error.response?.data?.error ||
              "Unable to delete the attachment."
          );

          return;
        }
      }

      updateSession(
        sessions.activeSessionId,
        currentSession => ({
          ...currentSession,
          attachments: (
            currentSession.attachments ||
            []
          ).filter(
            item =>
              item.localId !==
              attachment.localId
          )
        })
      );
    };


  const streamResponse = async (
    text,
    sessionId,
    messageId
  ) => {
    let currentText = "";

    for (
      let index = 0;
      index < text.length;
      index += 1
    ) {
      currentText += text[index];

      const streamedText = currentText;

      updateSession(
        sessionId,
        currentSession => ({
          ...currentSession,
          messages:
            currentSession.messages.map(
              message =>
                message.id === messageId
                  ? {
                      ...message,
                      content:
                        streamedText
                    }
                  : message
            )
        })
      );

      await new Promise(resolve =>
        setTimeout(resolve, 10)
      );
    }
  };


  const handleSearch = async () => {
    if (
      !query.trim() ||
      loading ||
      uploading
    ) {
      return;
    }

    const sessionId =
      sessions.activeSessionId;

    const currentSession =
      sessions.sessions.find(
        session =>
          session.sessionId === sessionId
      );

    if (!currentSession) {
      return;
    }

    const hasPendingAttachment =
      (
        currentSession.attachments || []
      ).some(
        attachment =>
          attachment.status ===
          "uploading"
      );

    if (hasPendingAttachment) {
      setUploadError(
        "Allow the attachment upload to finish before sending the message."
      );

      return;
    }

    const readyAttachments =
      (
        currentSession.attachments || []
      ).filter(
        attachment =>
          attachment.status === "ready" &&
          attachment.attachmentId
      );

    const submittedQuery =
      query.trim();

    const userMessage = {
      id: generateId(),
      role: "user",
      content: submittedQuery,
      timestamp: getTimestamp(),
      attachments:
        readyAttachments.map(
          attachment => ({
            attachmentId:
              attachment.attachmentId,
            filename:
              attachment.filename
          })
        )
    };

    const assistantMessage = {
      id: generateId(),
      role: "assistant",
      content: "",
      timestamp: getTimestamp()
    };

    const requestMessages = [
      ...currentSession.messages,
      userMessage
    ];

    setLoading(true);
    setUploadError("");
    setQuery("");

    updateSession(
      sessionId,
      session => ({
        ...session,
        title:
          session.title === "New Chat"
            ? submittedQuery.substring(
                0,
                25
              )
            : session.title,
        messages: [
          ...requestMessages,
          assistantMessage
        ]
      })
    );

    try {
      const response = await axios.post(
        `${API_BASE_URL}/chat`,
        {
          session_id: sessionId,
          messages:
            requestMessages.map(
              message => ({
                role: message.role,
                content: message.content
              })
            ),
          attachment_ids:
            readyAttachments.map(
              attachment =>
                attachment.attachmentId
            )
        }
      );

      const botReply =
        response.data?.reply ||
        response.data?.error ||
        "No response from server.";

      await streamResponse(
        botReply,
        sessionId,
        assistantMessage.id
      );
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.error ||
        "Error fetching response.";

      updateSession(
        sessionId,
        session => ({
          ...session,
          messages:
            session.messages.map(
              message =>
                message.id ===
                assistantMessage.id
                  ? {
                      ...message,
                      content:
                        errorMessage
                    }
                  : message
            )
        })
      );
    } finally {
      setLoading(false);
    }
  };


  const clearChat = () => {
    updateSession(
      sessions.activeSessionId,
      currentSession => ({
        ...currentSession,
        messages: []
      })
    );

    setQuery("");
  };


  return (
    <div className="app-container">
      <aside
        className={`sidebar ${
          sidebarOpen ? "open" : ""
        }`}
      >
        <button
          type="button"
          className="new-chat-btn"
          onClick={createNewChat}
        >
          + New Chat
        </button>

        <div className="session-list">
          {sessions.sessions.map(
            session => (
              <div
                key={session.sessionId}
                className={`session-item ${
                  session.sessionId ===
                  sessions.activeSessionId
                    ? "active"
                    : ""
                }`}
              >
                <button
                  type="button"
                  className="session-title"
                  onClick={() =>
                    switchSession(
                      session.sessionId
                    )
                  }
                >
                  {session.title}
                </button>

                <button
                  type="button"
                  className="session-menu-btn"
                  onClick={event => {
                    event.stopPropagation();

                    setOpenMenuSessionId(
                      openMenuSessionId ===
                        session.sessionId
                        ? null
                        : session.sessionId
                    );
                  }}
                  aria-label="Chat options"
                >
                  ⋮
                </button>

                {openMenuSessionId ===
                  session.sessionId && (
                  <div className="session-dropdown">
                    <button
                      type="button"
                      onClick={() =>
                        renameSession(
                          session.sessionId
                        )
                      }
                    >
                      Rename
                    </button>

                    <button
                      type="button"
                      className="delete-option"
                      onClick={() =>
                        deleteSession(
                          session.sessionId
                        )
                      }
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            )
          )}
        </div>
      </aside>

      {sidebarOpen && (
        <button
          type="button"
          className="overlay"
          aria-label="Close sidebar"
          onClick={() =>
            setSidebarOpen(false)
          }
        />
      )}

      <main className="main-content">
        <header className="header">
          <div className="header-left">
            <button
              type="button"
              className="menu-btn"
              onClick={() =>
                setSidebarOpen(
                  previous => !previous
                )
              }
              aria-label="Open sidebar"
            >
              ☰
            </button>

            <h1>Synapse</h1>
          </div>

          <button
            type="button"
            className="clear-chat-btn"
            onClick={clearChat}
          >
            Clear Chat
          </button>
        </header>

        <section className="chat-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h2>Start a conversation</h2>

              <p>
                Ask a question or attach a
                document to search its
                contents.
              </p>
            </div>
          ) : (
            messages.map(message => (
              <article
                key={message.id}
                className={`chat-bubble ${
                  message.role === "user"
                    ? "user"
                    : "bot"
                }`}
              >
                {message.attachments?.length >
                  0 && (
                  <div className="message-attachments">
                    {message.attachments.map(
                      attachment => (
                        <span
                          key={
                            attachment.attachmentId
                          }
                          className="message-attachment"
                        >
                          <span aria-hidden="true">
                            📎
                          </span>

                          {attachment.filename}
                        </span>
                      )
                    )}
                  </div>
                )}

                {message.role ===
                "assistant" ? (
                  message.content ? (
                    <ReactMarkdown
                      remarkPlugins={[
                        remarkGfm
                      ]}
                      components={{
                        code({
                          inline,
                          className,
                          children,
                          ...props
                        }) {
                          const match =
                            /language-(\w+)/.exec(
                              className ||
                                ""
                            );

                          if (
                            !inline &&
                            match
                          ) {
                            return (
                              <SyntaxHighlighter
                                style={oneDark}
                                language={
                                  match[1]
                                }
                                PreTag="div"
                                customStyle={{
                                  overflowX:
                                    "auto",
                                  borderRadius:
                                    "8px",
                                  margin:
                                    "12px 0"
                                }}
                                {...props}
                              >
                                {String(
                                  children
                                ).replace(
                                  /\n$/,
                                  ""
                                )}
                              </SyntaxHighlighter>
                            );
                          }

                          return (
                            <code
                              className={
                                className
                              }
                              {...props}
                            >
                              {children}
                            </code>
                          );
                        }
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <span className="typing-indicator">
                      Thinking...
                    </span>
                  )
                ) : (
                  <div>
                    {message.content}
                  </div>
                )}
              </article>
            ))
          )}

          <div ref={bottomRef} />
        </section>

        <footer className="composer">
          {attachments.length > 0 && (
            <div className="attachment-list">
              {attachments.map(
                attachment => (
                  <div
                    key={attachment.localId}
                    className={`attachment-chip attachment-${attachment.status}`}
                  >
                    <span
                      className="attachment-icon"
                      aria-hidden="true"
                    >
                      📎
                    </span>

                    <div className="attachment-details">
                      <span className="attachment-name">
                        {attachment.filename}
                      </span>

                      <span className="attachment-status">
                        {attachment.status ===
                          "uploading" &&
                          "Uploading and indexing..."}

                        {attachment.status ===
                          "ready" &&
                          `${formatFileSize(
                            attachment.size
                          )} • Ready`}

                        {attachment.status ===
                          "failed" &&
                          (attachment.error ||
                            "Upload failed")}
                      </span>
                    </div>

                    <button
                      type="button"
                      className="remove-attachment-btn"
                      disabled={
                        attachment.status ===
                        "uploading"
                      }
                      onClick={() =>
                        removeAttachment(
                          attachment
                        )
                      }
                      aria-label={`Remove ${attachment.filename}`}
                    >
                      ×
                    </button>
                  </div>
                )
              )}
            </div>
          )}

          {uploadError && (
            <div
              className="upload-error"
              role="alert"
            >
              {uploadError}
            </div>
          )}

          <div className="input-section">
            <input
              ref={fileInputRef}
              className="attachment-file-input"
              type="file"
              accept=".pdf,.docx,.txt,.csv"
              multiple
              onChange={
                handleFileSelection
              }
            />

            <button
              type="button"
              className="attachment-btn"
              onClick={openFilePicker}
              disabled={
                loading || uploading
              }
              aria-label="Attach files"
              title="Attach PDF, DOCX, TXT, or CSV"
            >
              {uploading ? (
                <span className="button-spinner" />
              ) : (
                <span aria-hidden="true">
                  📎
                </span>
              )}
            </button>

            <input
              className="message-input"
              type="text"
              placeholder={
                uploading
                  ? "Uploading attachment..."
                  : "Send a message..."
              }
              value={query}
              disabled={uploading}
              onChange={event =>
                setQuery(
                  event.target.value
                )
              }
              onKeyDown={event => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  query.trim() &&
                  !loading &&
                  !uploading
                ) {
                  event.preventDefault();
                  handleSearch();
                }
              }}
            />

            <button
              type="button"
              className="send-btn"
              onClick={handleSearch}
              disabled={
                loading ||
                uploading ||
                !query.trim()
              }
            >
              {loading
                ? "Sending..."
                : "Send"}
            </button>
          </div>
        </footer>
      </main>
    </div>
  );
}


export default App;