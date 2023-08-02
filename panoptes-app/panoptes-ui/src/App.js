import logo from './logo.png';
import uploadimg from './upload.png';
import thumbnail from './thumbnail.jpg'
import './App.css';
import axios from 'axios';
import AWS from 'aws-sdk';
import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Container, Row, Col, Button, Form, Image, ListGroup, Card } from 'react-bootstrap';
import Cookies from 'js-cookie';

function Loading() {
    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <div style={{
                border: '16px solid #f3f3f3',
                borderRadius: '50%',
                borderTop: '16px solid #3498db',
                width: '120px',
                height: '120px',
                animation: 'spin 2s linear infinite'
            }} />
            <style jsx>{`
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}

function ErrorDisplayComponent({ message }) {
    return (
        <Col className="d-flex justify-content-center">
            <Card style={{ width: '80%', padding: '20px', borderRadius: '15px', textAlign: 'center', background: 'rgb(0 15 50)' }}>                
                <Card.Body>
                    <Card.Title style={{ color: 'red', fontFamily: 'Arial, sans-serif' }}>{message}</Card.Title>
                </Card.Body>
            </Card>
        </Col>
    );
}

function LogoComponent() {
  return (
    <Col className="d-flex justify-content-left">
        <Card style={{
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'center',
            borderRadius: '20px',
            background: 'linear-gradient(to right, rgb(56,178,165), rgb(0,0,30) 20%)',
            backgroundSize: '200% 100%',
            margin: '30px'
        }}>
            <Image src={logo} alt="Logo" style={{ maxWidth: '100px', height: 'auto' }} />
            <Card.Body>
                <Card.Title style={{ color: 'white', fontFamily: 'Poppins, sans-serif' }}><h3>Panoptes.ai</h3></Card.Title>
            </Card.Body>
        </Card>
    </Col>
);
}

function VideoUploadComponent({ onUpload }) {
  const { getRootProps, getInputProps } = useDropzone({
      accept: 'video/*',
      onDrop: (acceptedFiles) => {
          onUpload(acceptedFiles[0]);
      }
  });

  return (
      <Col className="d-flex justify-content-center">
          <Card style={{ width: '80%', padding: '20px', borderRadius: '15px', textAlign: 'center', background: 'rgb(0 15 50)' }}>
              <div {...getRootProps()} style={{ border: '2px dashed #007bff', padding: '20px', borderRadius: '15px' }}>
                  <input {...getInputProps()} />
                  <Image src={uploadimg} alt="Upload" style={{ maxWidth: '100px', height: 'auto' }} />
                  <p>Drag 'n' drop a video here, or click to select</p>
              </div>
          </Card>
      </Col>
  );
}


function TextSearchComponent({ onSearch }) {
  const [searchText, setSearchText] = useState("");

  const handleSubmit = () => {
      onSearch(searchText);
  };

  return (
      <Col className="text-center">
          <Form.Control type="text" value={searchText} onChange={e => setSearchText(e.target.value)} style={{ borderRadius: '15px', background: 'linear-gradient(to right, rgb(56,178,165), rgb(0,0,30) 20%)', color: 'white'}} />
          <Button onClick={handleSubmit} style={{ marginLeft: '10px' }}>Search</Button>
      </Col>
  );
}

function UploadSection({ onUpload }) {
  return (
      <Container>
          <Row><LogoComponent /></Row>
          <Row><VideoUploadComponent onUpload={onUpload} /></Row>
      </Container>
  );
}

function SearchSection({ onSearch, videoTimestamps, loading, searchClicked }) {
  return (
    <Container>
        <Row><LogoComponent /></Row>
        <Row><TextSearchComponent onSearch={onSearch} /></Row>
        <Row>{searchClicked && <VideoTimestampDisplayComponent videoTimestamps={videoTimestamps} loading={loading} />}</Row>
    </Container>
);
}

function App() {
  const [currentPage, setCurrentPage] = useState(1);
  const [videoTimestamps, setVideoTimestamps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [bucketName, setBucketName] = useState('');
  const [error, setError] = useState(null);
  const [searchClicked, setSearchClicked] = useState(false);

  useEffect(() => {
    const createBucket = async () => {
        setLoading(true);
        let userId;
        try {
            userId = Cookies.get('userId');
            if (!userId) {
                const response = await axios.get('http://localhost:3001/generate-userid');
                if (response.data.success) {
                    userId = response.data.userId;
                    Cookies.set('userId', userId);
                } else {
                    setTimeout(() => {
                        setLoading(false);
                    }, 2000);
                    setError('Error generating user ID from server');
                    return;
                }
            }
        } catch(error) {
            console.error("Error calling userid service:", error);
            setTimeout(() => {
                setLoading(false);
            }, 2000);
            setError('Error calling userid generation service');
            return;
        }
        try {
            let bucketName = Cookies.get('panoptes-bucketName');
            if (!bucketName) {
                const response = await axios.post('http://localhost:3001/create-bucket', { userId });
                if (response.data.success) {
                    bucketName = response.data.bucketName;
                    Cookies.set('panoptes-bucketName', bucketName);
                    setBucketName(bucketName);
                    setCurrentPage(1);
                } else {
                    setError('No available storage');
                }
            } else {
                setBucketName(bucketName);
                setCurrentPage(1);
            }
        } catch (error) {
            console.error("Error calling Storage creation service:", error);
            setError('Error calling Storage creation service');
        } finally {
            setTimeout(() => {
                setLoading(false);
            }, 2000);
        }
    };
    createBucket();
}, []);

const handleUpload = async (file) => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('bucketName', bucketName);
    try {
        const response = await axios.post('http://localhost:3001/indexvideo', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });

        if (response.data.success) {
            console.log("Video uploaded successfully");
            setCurrentPage(2);
        } else {
            setError('Error uploading video');
            console.error("Error uploading video:", response.data.message);
        }
    } catch (error) {
        setError('Error calling Video upload service');
        console.error("Error uploading video:", error);
    } finally {
        setTimeout(() => {
            setLoading(false);
        }, 2000);
    }
};

  const handleSearch = async (searchText) => {
    setLoading(true);
    setSearchClicked(true);
    try {
        const response = await axios.get('http://localhost:3001/search', {
            params: {
                query: searchText
            }
        });
        setVideoTimestamps(response.data);
    } catch (error) {
        console.error("Error searching for videos:", error);
    } finally {
        setTimeout(() => {
            setLoading(false);
        }, 3000);
    }
};

  if (loading) {
      return <Loading />;
  }

  if (error) {
    return(
    <div className="App">
         <Container>
            <Row><LogoComponent /></Row>
            <ErrorDisplayComponent message={error} />
        </Container>
    </div>
    )
  }

  return (
    <div className="App">
        {currentPage === 1 ? (
                <UploadSection onUpload={handleUpload} />
            ) : (
                <SearchSection onSearch={handleSearch} videoTimestamps={videoTimestamps} loading={loading} searchClicked={searchClicked} />
            )}
    </div>
  );
}

function VideoTimestampDisplayComponent({ videoTimestamps, loading, condition}) {
    if (loading) {
        return <Loading />;
    }
    return (
        <Col className="text-center">
            <ListGroup>
                    <ListGroup.Item key={1} style={{ border: '1px solid #007bff', borderRadius: '15px', margin: '10px', background: 'rgb(0 15 50)' }}>
                        <Card style={{ width: '18rem', margin:'10px' }}>
                            <Card.Img variant="top" src={thumbnail} alt="Thumbnail" />
                            <Card.Body>
                                <Card.Title>Timestamp: 0:00 - 0:03</Card.Title>
                                <Card.Text>Confidence: 0.2645</Card.Text>
                            </Card.Body>
                        </Card>
                    </ListGroup.Item>
            </ListGroup>
        </Col>
    );
  }

export default App;
