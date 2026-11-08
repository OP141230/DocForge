// Conversation types (mirror backend Pydantic models)

export interface MessageAttachment {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  data_url: string;  // base64-encoded data URL
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  attachments: MessageAttachment[];
  sequence_number: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
}

export interface CreateConversationRequest {
  title: string;
}

export interface CreateMessageRequest {
  role: 'user' | 'assistant';
  content: string;
  attachments?: MessageAttachment[];
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
  limit: number;
  offset: number;
}

export interface MessageListResponse {
  messages: Message[];
  total: number;
  limit: number;
  offset: number;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}
