// ================================================================
// APP.JS - REACT NATIVE MOBILE APP
// ================================================================

import React, { useState, useEffect, useRef } from 'react';
import {
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  View,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Modal,
  Alert,
  ScrollView,
  Linking
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { io } from 'socket.io-client';

// ===== CẤU HÌNH =====
const API_URL = 'http://your-server.com:5000';
const SOCKET_URL = 'http://your-server.com:5000';

// ===== LEVEL NAMES =====
const LEVEL_NAMES = {
  basic: 'AI Thường',
  pro: 'AI Pro',
  plus: 'AI Plus',
  pro3: 'AI 3.0 Pro'
};

// ===== COMPONENT CHÍNH =====
const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [level, setLevel] = useState('pro');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [showMusicModal, setShowMusicModal] = useState(false);
  const [musicPrompt, setMusicPrompt] = useState('');
  const [musicStyle, setMusicStyle] = useState('pop');
  const socketRef = useRef(null);
  const flatListRef = useRef(null);

  // ===== SOCKET.IO =====
  useEffect(() => {
    if (isLoggedIn) {
      socketRef.current = io(SOCKET_URL);
      socketRef.current.on('connect', () => {
        console.log('✅ Connected to socket');
        socketRef.current.emit('join', { room: 'global' });
      });
      socketRef.current.on('new_message', (data) => {
        if (data.message) {
          setMessages(prev => [...prev, {
            role: 'ai',
            content: data.message,
            time: new Date().toISOString()
          }]);
        }
      });
    }
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [isLoggedIn]);

  // ===== CHECK LOGIN =====
  useEffect(() => {
    checkLogin();
  }, []);

  const checkLogin = async () => {
    try {
      const token = await AsyncStorage.getItem('user_token');
      if (token) {
        const response = await fetch(`${API_URL}/api/auth/me`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        if (!data.error) {
          setUser(data);
          setIsLoggedIn(true);
          setShowLogin(false);
          loadConversations();
        } else {
          setShowLogin(true);
        }
      } else {
        setShowLogin(true);
      }
    } catch (error) {
      setShowLogin(true);
    }
  };

  // ===== LOGIN =====
  const loginWithGoogle = () => {
    Alert.prompt('Đăng nhập Google', 'Nhập email của bạn:', [
      { text: 'Hủy', style: 'cancel' },
      {
        text: 'Đăng nhập',
        onPress: async (emailInput) => {
          try {
            const response = await fetch(`${API_URL}/api/auth/google`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ id_token: emailInput })
            });
            const data = await response.json();
            if (data.success) {
              await AsyncStorage.setItem('user_token', data.user.id);
              setUser(data.user);
              setIsLoggedIn(true);
              setShowLogin(false);
              loadConversations();
            } else {
              Alert.alert('Lỗi', data.error || 'Đăng nhập thất bại');
            }
          } catch (error) {
            Alert.alert('Lỗi', 'Không thể kết nối server');
          }
        }
      }
    ]);
  };

  // ===== LOGOUT =====
  const logout = async () => {
    await AsyncStorage.removeItem('user_token');
    setIsLoggedIn(false);
    setUser(null);
    setMessages([]);
    setConversations([]);
    setShowLogin(true);
  };

  // ===== SEND MESSAGE =====
  const sendMessage = async () => {
    if (!inputText.trim() || !isLoggedIn) return;

    const userMessage = {
      role: 'user',
      content: inputText,
      time: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputText,
          conversation_id: currentConversationId,
          level: level
        })
      });
      const data = await response.json();

      if (data.error) {
        Alert.alert('Lỗi', data.error);
        if (data.limit_reached) {
          setShowUpgrade(true);
        }
      } else {
        if (data.conversation_id) {
          setCurrentConversationId(data.conversation_id);
        }
        setMessages(prev => [...prev, {
          role: 'ai',
          content: data.message || 'Đã xử lý thành công.',
          time: new Date().toISOString()
        }]);
      }
    } catch (error) {
      Alert.alert('Lỗi', 'Không thể kết nối server');
    }
    setIsLoading(false);
  };

  // ===== LOAD CONVERSATIONS =====
  const loadConversations = async () => {
    try {
      const response = await fetch(`${API_URL}/conversations`);
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  // ===== LOAD CONVERSATION =====
  const loadConversation = async (id) => {
    try {
      const response = await fetch(`${API_URL}/conversation/${id}`);
      const data = await response.json();
      if (data.conversation) {
        setMessages(data.conversation.messages || []);
        setCurrentConversationId(id);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  // ===== GENERATE MUSIC =====
  const generateMusic = async () => {
    if (!musicPrompt.trim()) {
      Alert.alert('Lỗi', 'Vui lòng nhập mô tả bài hát');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/generate_music`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: musicPrompt,
          style: musicStyle
        })
      });
      const data = await response.json();

      if (data.error) {
        Alert.alert('Lỗi', data.error);
      } else if (data.audio_url) {
        Alert.alert('🎵 Thành công', `Bài hát "${data.title}" đã được tạo!`);
        setShowMusicModal(false);
        setMusicPrompt('');
      } else {
        Alert.alert('Thông báo', 'Bài hát đã được tạo nhưng chưa có link nghe.');
      }
    } catch (error) {
      Alert.alert('Lỗi', 'Không thể kết nối server');
    }
    setIsLoading(false);
  };

  // ===== RENDER MESSAGE =====
  const renderMessage = ({ item }) => (
    <View style={[
      styles.messageContainer,
      item.role === 'user' ? styles.userMessage : styles.aiMessage
    ]}>
      <Text style={[
        styles.messageText,
        item.role === 'user' ? styles.userText : styles.aiText
      ]}>
        {item.content}
      </Text>
      <Text style={styles.messageTime}>
        {new Date(item.time).toLocaleTimeString()}
      </Text>
    </View>
  );

  // ===== RENDER =====
  if (!isLoggedIn) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loginContainer}>
          <Text style={styles.loginTitle}>🔐 T.VỸ-AI</Text>
          <Text style={styles.loginSubtitle}>Đăng nhập để tiếp tục</Text>
          <TouchableOpacity style={styles.loginButton} onPress={loginWithGoogle}>
            <Text style={styles.loginButtonText}>Đăng nhập với Google</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>T.VỸ-AI</Text>
            <Text style={styles.headerLevel}>{LEVEL_NAMES[level] || 'AI Pro'}</Text>
          </View>
          <View style={styles.headerActions}>
            <TouchableOpacity onPress={() => setShowMusicModal(true)}>
              <Text style={styles.headerIcon}>🎵</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setShowUpgrade(true)}>
              <Text style={styles.headerIcon}>⭐</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={logout}>
              <Text style={styles.headerIcon}>🚪</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Messages */}
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item, index) => index.toString()}
          style={styles.messagesList}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
        />

        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Nhập câu hỏi..."
            multiline
          />
          <TouchableOpacity
            style={styles.sendButton}
            onPress={sendMessage}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.sendButtonText}>Gửi</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Upgrade Modal */}
        <Modal visible={showUpgrade} transparent animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Nâng cấp AI</Text>
              <TouchableOpacity style={styles.closeButton} onPress={() => setShowUpgrade(false)}>
                <Text style={styles.closeButtonText}>✕</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.upgradeOption} onPress={() => {
                setLevel('pro');
                setShowUpgrade(false);
                Alert.alert('Thành công', 'Đã nâng cấp lên AI Pro!');
              }}>
                <Text style={styles.upgradeOptionTitle}>🔵 AI Pro</Text>
                <Text style={styles.upgradeOptionPrice}>20.000đ/tháng</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.upgradeOption} onPress={() => {
                setLevel('plus');
                setShowUpgrade(false);
                Alert.alert('Thành công', 'Đã nâng cấp lên AI Plus!');
              }}>
                <Text style={styles.upgradeOptionTitle}>🟣 AI Plus</Text>
                <Text style={styles.upgradeOptionPrice}>50.000đ/tháng</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.upgradeOption} onPress={() => {
                setLevel('pro3');
                setShowUpgrade(false);
                Alert.alert('Thành công', 'Đã nâng cấp lên AI 3.0 Pro!');
              }}>
                <Text style={styles.upgradeOptionTitle}>🔴 AI 3.0 Pro</Text>
                <Text style={styles.upgradeOptionPrice}>100.000đ/tháng</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>

        {/* Music Modal */}
        <Modal visible={showMusicModal} transparent animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>🎵 Tạo nhạc bằng AI</Text>
              <TouchableOpacity style={styles.closeButton} onPress={() => setShowMusicModal(false)}>
                <Text style={styles.closeButtonText}>✕</Text>
              </TouchableOpacity>

              <Text style={styles.musicLabel}>Mô tả bài hát:</Text>
              <TextInput
                style={styles.musicInput}
                value={musicPrompt}
                onChangeText={setMusicPrompt}
                placeholder="VD: Bài hát về tình yêu mùa hè..."
                multiline
              />

              <Text style={styles.musicLabel}>Thể loại:</Text>
              <View style={styles.musicStyleContainer}>
                {['pop', 'rock', 'jazz', 'edm', 'classical'].map((s) => (
                  <TouchableOpacity
                    key={s}
                    style={[styles.musicStyleBtn, musicStyle === s && styles.musicStyleBtnActive]}
                    onPress={() => setMusicStyle(s)}
                  >
                    <Text style={[styles.musicStyleText, musicStyle === s && styles.musicStyleTextActive]}>
                      {s.toUpperCase()}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity
                style={styles.musicGenerateBtn}
                onPress={generateMusic}
                disabled={isLoading}
              >
                <Text style={styles.musicGenerateBtnText}>
                  {isLoading ? 'Đang tạo...' : '🎵 Tạo nhạc'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

// ===== STYLES =====
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
  loginContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  loginTitle: { fontSize: 32, fontWeight: '700', color: '#2d3b8a' },
  loginSubtitle: { fontSize: 16, color: '#8a8aaa', marginTop: 8, marginBottom: 30 },
  loginButton: { backgroundColor: '#2d3b8a', padding: 14, borderRadius: 8, width: '100%' },
  loginButtonText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e4e7ec' },
  headerTitle: { fontSize: 18, fontWeight: '600', color: '#2d3b8a' },
  headerLevel: { fontSize: 12, color: '#8a8aaa' },
  headerActions: { flexDirection: 'row', gap: 16 },
  headerIcon: { fontSize: 20, marginHorizontal: 4 },
  messagesList: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  messageContainer: { maxWidth: '80%', marginBottom: 12, padding: 12, borderRadius: 12 },
  userMessage: { alignSelf: 'flex-end', backgroundColor: '#2d3b8a' },
  aiMessage: { alignSelf: 'flex-start', backgroundColor: '#fff', borderWidth: 1, borderColor: '#e4e7ec' },
  messageText: { fontSize: 14, lineHeight: 20 },
  userText: { color: '#fff' },
  aiText: { color: '#1a1a2e' },
  messageTime: { fontSize: 10, color: '#8a8aaa', marginTop: 4, alignSelf: 'flex-end' },
  inputContainer: { flexDirection: 'row', padding: 12, backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#e4e7ec', alignItems: 'flex-end' },
  input: { flex: 1, minHeight: 40, maxHeight: 100, backgroundColor: '#f8f9fa', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 8, fontSize: 14 },
  sendButton: { backgroundColor: '#2d3b8a', paddingHorizontal: 20, paddingVertical: 10, borderRadius: 20, marginLeft: 8 },
  sendButtonText: { color: '#fff', fontWeight: '600' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { width: '90%', backgroundColor: '#fff', borderRadius: 12, padding: 20 },
  modalTitle: { fontSize: 20, fontWeight: '700', textAlign: 'center', marginBottom: 16 },
  closeButton: { position: 'absolute', top: 12, right: 16 },
  closeButtonText: { fontSize: 20, color: '#8a8aaa' },
  upgradeOption: { flexDirection: 'row', justifyContent: 'space-between', padding: 14, borderBottomWidth: 1, borderBottomColor: '#e4e7ec' },
  upgradeOptionTitle: { fontSize: 16, fontWeight: '500' },
  upgradeOptionPrice: { fontSize: 14, fontWeight: '600', color: '#2d3b8a' },
  musicLabel: { fontSize: 14, fontWeight: '600', marginTop: 12, marginBottom: 4 },
  musicInput: { backgroundColor: '#f8f9fa', borderRadius: 8, padding: 12, fontSize: 14, minHeight: 60, borderWidth: 1, borderColor: '#e4e7ec' },
  musicStyleContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginVertical: 8 },
  musicStyleBtn: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20, backgroundColor: '#f8f9fa', borderWidth: 1, borderColor: '#e4e7ec' },
  musicStyleBtnActive: { backgroundColor: '#2d3b8a', borderColor: '#2d3b8a' },
  musicStyleText: { fontSize: 12, color: '#8a8aaa' },
  musicStyleTextActive: { color: '#fff' },
  musicGenerateBtn: { backgroundColor: '#2d3b8a', padding: 14, borderRadius: 8, marginTop: 16 },
  musicGenerateBtnText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
});

export default App;