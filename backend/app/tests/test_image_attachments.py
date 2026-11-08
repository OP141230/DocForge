"""
Tests for image attachments in conversation messages.
"""
import pytest
import base64
from datetime import datetime

from app.models.auth import Message, MessageAttachment, Conversation
from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository


@pytest.fixture
async def conversation(test_db, user):
    """Create a test conversation."""
    repo = ConversationRepository(test_db)
    return await repo.create(user_id=user.id, title="Test Conversation")


@pytest.mark.asyncio
async def test_message_with_single_image(test_db, user, conversation):
    """Test creating a message with one image attachment."""
    repo = MessageRepository(test_db)
    
    # Create a small test image (1x1 red pixel PNG)
    test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    data_url = f"data:image/png;base64,{test_image_data}"
    
    attachment = MessageAttachment(
        filename="test.png",
        mime_type="image/png",
        size_bytes=len(test_image_data),
        data_url=data_url
    )
    
    message = await repo.create(
        conversation_id=conversation.id,
        role="user",
        content="Check out this image!",
        sequence_number=1,
        attachments=[attachment]
    )
    
    assert message.id is not None
    assert message.content == "Check out this image!"
    assert len(message.attachments) == 1
    assert message.attachments[0].filename == "test.png"
    assert message.attachments[0].mime_type == "image/png"
    assert message.attachments[0].data_url == data_url


@pytest.mark.asyncio
async def test_message_with_multiple_images(test_db, user, conversation):
    """Test creating a message with multiple image attachments."""
    repo = MessageRepository(test_db)
    
    # Create two test images
    test_image_1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    test_image_2 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    
    attachments = [
        MessageAttachment(
            filename="image1.png",
            mime_type="image/png",
            size_bytes=len(test_image_1),
            data_url=f"data:image/png;base64,{test_image_1}"
        ),
        MessageAttachment(
            filename="image2.png",
            mime_type="image/png",
            size_bytes=len(test_image_2),
            data_url=f"data:image/png;base64,{test_image_2}"
        )
    ]
    
    message = await repo.create(
        conversation_id=conversation.id,
        role="user",
        content="Two images",
        sequence_number=1,
        attachments=attachments
    )
    
    assert len(message.attachments) == 2
    assert message.attachments[0].filename == "image1.png"
    assert message.attachments[1].filename == "image2.png"


@pytest.mark.asyncio
async def test_message_without_attachments(test_db, user, conversation):
    """Test creating a message without attachments (backward compatibility)."""
    repo = MessageRepository(test_db)
    
    message = await repo.create(
        conversation_id=conversation.id,
        role="user",
        content="No images here",
        sequence_number=1,
        attachments=[]
    )
    
    assert message.content == "No images here"
    assert len(message.attachments) == 0


@pytest.mark.asyncio
async def test_list_messages_with_attachments(test_db, user, conversation):
    """Test listing messages preserves attachments."""
    repo = MessageRepository(test_db)
    
    # Create a message with an attachment
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    attachment = MessageAttachment(
        filename="test.png",
        mime_type="image/png",
        size_bytes=len(test_image),
        data_url=f"data:image/png;base64,{test_image}"
    )
    
    await repo.create(
        conversation_id=conversation.id,
        role="user",
        content="Image message",
        sequence_number=1,
        attachments=[attachment]
    )
    
    # Create a message without attachments
    await repo.create(
        conversation_id=conversation.id,
        role="assistant",
        content="Text message",
        sequence_number=2,
        attachments=[]
    )
    
    # List messages
    messages, total = await repo.list_by_conversation(conversation.id)
    
    assert total == 2
    assert len(messages[0].attachments) == 1
    assert messages[0].attachments[0].filename == "test.png"
    assert len(messages[1].attachments) == 0


@pytest.mark.asyncio
async def test_message_attachment_validation(test_db, user, conversation):
    """Test that attachment fields are properly validated."""
    repo = MessageRepository(test_db)
    
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    
    attachment = MessageAttachment(
        filename="test.png",
        mime_type="image/png",
        size_bytes=len(test_image),
        data_url=f"data:image/png;base64,{test_image}"
    )
    
    message = await repo.create(
        conversation_id=conversation.id,
        role="user",
        content="Test",
        sequence_number=1,
        attachments=[attachment]
    )
    
    # Verify all fields are present
    saved_attachment = message.attachments[0]
    assert saved_attachment.id is not None
    assert saved_attachment.filename == "test.png"
    assert saved_attachment.mime_type == "image/png"
    assert saved_attachment.size_bytes == len(test_image)
    assert saved_attachment.data_url.startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_assistant_message_with_images(test_db, user, conversation):
    """Test that assistant messages can also have image attachments (for generated diagrams, etc)."""
    repo = MessageRepository(test_db)
    
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    attachment = MessageAttachment(
        filename="generated_diagram.png",
        mime_type="image/png",
        size_bytes=len(test_image),
        data_url=f"data:image/png;base64,{test_image}"
    )
    
    message = await repo.create(
        conversation_id=conversation.id,
        role="assistant",
        content="Here's the diagram you requested:",
        sequence_number=1,
        attachments=[attachment]
    )
    
    assert message.role == "assistant"
    assert len(message.attachments) == 1
    assert message.attachments[0].filename == "generated_diagram.png"


@pytest.mark.asyncio
async def test_image_with_jpeg_mime_type(test_db, user, conversation):
    """Test that JPEG images are properly stored."""
    repo = MessageRepository(test_db)
    
    # Small JPEG test data
    test_jpeg = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlbaWmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9/KKKKAP/2Q=="
    
    attachment = MessageAttachment(
        filename="photo.jpg",
        mime_type="image/jpeg",
        size_bytes=len(test_jpeg),
        data_url=f"data:image/jpeg;base64,{test_jpeg}"
    )
    
    message = await repo.create(
        conversation_id=conversation.id,
        role="user",
        content="Photo",
        sequence_number=1,
        attachments=[attachment]
    )
    
    assert message.attachments[0].mime_type == "image/jpeg"
    assert message.attachments[0].filename == "photo.jpg"
