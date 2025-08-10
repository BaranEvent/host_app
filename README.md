# Event Management Dashboard

A comprehensive Streamlit application for managing events, features, and registration forms. This application provides a complete solution for event organizers to create, manage, and configure events with various features.

## Features

### 🏠 Home Dashboard
- **Current Events**: Shows events that are currently active (between start and end dates)
- **Upcoming Events**: Displays future events (start date > current timestamp)
- **Past Events**: Lists completed events (end date < current timestamp)
- **Event Creation**: Quick access to create new events
- **Host ID Management**: Filter events by host ID

### 🎉 Event Creation
- Comprehensive event registration form
- Event type selection with predefined categories
- Location and address management
- Date and time scheduling
- Capacity planning
- Visibility controls
- Real-time form validation

### ⚙️ Feature Management
- **Before Event Features**: Registration forms, pre-event surveys
- **During Event Features**: Live polling, real-time feedback
- **After Event Features**: Post-event surveys, feedback collection
- Feature activation and configuration
- Integration with form builder

### 📝 Form Builder
- Drag-and-drop question management
- Multiple question types:
  - Text input
  - Number input
  - Date/time picker
  - Boolean (Yes/No)
  - Single choice
  - Multiple choice
- Required field validation
- Form preview functionality
- Question reordering

## Project Structure

```
host_app/
├── app.py                          # Main home dashboard
├── pages/
│   ├── event_creation.py           # Event creation form
│   ├── feature_management.py       # Feature management interface
│   └── form_builder.py             # Form builder tool
├── .streamlit/
│   ├── config.toml                 # Streamlit configuration
│   └── pages.toml                  # Page visibility settings
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd host_app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Airtable**:
   - Update the `AIRTABLE_CONFIG` in each file with your Airtable base ID and API key
   - Ensure you have the following tables in your Airtable base:
     - `events`: For storing event information
     - `event_features`: For managing feature configurations
     - `registration_form`: For storing form questions

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Usage

### 1. Home Dashboard
- Enter your Host ID in the sidebar to view your events
- Click "Etkinlik Oluştur" to create a new event
- View current, upcoming, and past events
- Access feature management for each event

### Navigation Flow
The application uses a controlled navigation flow:
1. **Home Dashboard** (`app.py`) - Main entry point
2. **Event Creation** (`pages/event_creation.py`) - Create new events
3. **Feature Management** (`pages/feature_management.py`) - Configure event features
4. **Form Builder** (`pages/form_builder.py`) - Create registration forms

Users cannot directly access pages from the sidebar - they must follow the proper navigation flow.

### 2. Event Creation
- Fill out the comprehensive event form
- Set event details, location, dates, and capacity
- Configure visibility settings
- Submit to create the event and get redirected to feature management

### 3. Feature Management
- Select features to enable for your event
- Configure registration forms
- Manage feature settings
- Navigate to form builder for detailed configuration

### 4. Form Builder
- Add questions to your registration form
- Choose from various question types
- Set required field indicators
- Preview the form before saving
- Save to Airtable

## Airtable Schema

### Events Table
- `name`: Event name
- `description`: Event description
- `type`: Event category
- `host_id`: Host identifier
- `location_name`: Venue name
- `detailed_address`: Full address
- `start_date`: Event start date/time
- `end_date`: Event end date/time
- `capacity`: Maximum attendees
- `is_visible`: Visibility flag
- `ID`: Auto-generated event ID

### Event Features Table
- `event_id`: Reference to event
- `feature_id`: Feature identifier
- `feature_key`: Feature type
- `enabled`: Feature status
- `is_active`: Active status

### Registration Form Table
- `event_id`: Reference to event
- `name`: Question text
- `type`: Question type
- `is_required`: Required field flag
- `rank`: Question order
- `possible_answers`: JSON string for multiple choice options

## Configuration

### Airtable Setup
1. Create a new Airtable base
2. Create the required tables with the specified fields
3. Generate an API key with appropriate permissions
4. Update the configuration in all Python files

### Environment Variables
For production deployment, consider using environment variables for sensitive data:
```python
import os

AIRTABLE_CONFIG = {
    "base_id": os.getenv("AIRTABLE_BASE_ID"),
    "api_key": os.getenv("AIRTABLE_API_KEY")
}
```

## Development

### Adding New Features
1. Update the `FEATURES` dictionary in `feature_management.py`
2. Add corresponding configuration pages
3. Update the navigation flow
4. Test the integration

### Customizing Question Types
1. Add new types to the `DATA_TYPES` dictionary in `form_builder.py`
2. Update the `render_question_preview` function
3. Add validation logic as needed

## Deployment

### Streamlit Cloud
1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Set environment variables for Airtable credentials
4. Deploy the application

### Local Deployment
1. Install dependencies
2. Configure Airtable credentials
3. Run with `streamlit run app.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Changelog

### Version 1.0.0
- Initial release
- Complete event management system
- Form builder functionality
- Feature management interface
- Multi-page application structure 