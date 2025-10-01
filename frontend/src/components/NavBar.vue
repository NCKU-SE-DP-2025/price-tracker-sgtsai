<template>
  <nav class="navbar" ref="navbar">
    <div class="title">
      <RouterLink to="/overview" @click="closeMenu">價格追蹤小幫手</RouterLink>
    </div>

    <div class="hamburger" @click="toggleMenu">
      <i class="bi bi-list" />
    </div>

    <ul :class="['options', { open: isMenuOpen }]">
      <li><RouterLink to="/overview" @click="closeMenu">物價概覽</RouterLink></li>
      <li><RouterLink to="/trending" @click="closeMenu">物價趨勢</RouterLink></li>
      <li><RouterLink to="/news" @click="closeMenu">相關新聞</RouterLink></li>
      <li v-if="!isLoggedIn"><RouterLink to="/login" @click="closeMenu">登入</RouterLink></li>
      <li v-else @click="handleLogout">Hi, {{ userName }}！登出</li>
    </ul>
  </nav>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'NavBar',
  setup() {
    const isMenuOpen = ref(false)
    const navbar = ref(null)

    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value
    }

    const closeMenu = () => {
      isMenuOpen.value = false
    }

    const handleClickOutside = (event) => {
      if (navbar.value && !navbar.value.contains(event.target)) {
        closeMenu()
      }
    }

    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
    })

    onBeforeUnmount(() => {
      document.removeEventListener('click', handleClickOutside)
    })

    const authStore = useAuthStore()
    const isLoggedIn = computed(() => authStore.isLoggedIn)
    const userName = computed(() => authStore.getUserName)

    const handleLogout = () => {
      authStore.logout()
      closeMenu()
    }

    const route = useRoute()
    watch(() => route.fullPath, closeMenu)

    return {
      isMenuOpen,
      toggleMenu,
      closeMenu,
      handleLogout,
      isLoggedIn,
      userName,
      navbar
    }
  }
}
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  background-color: #f3f3f3;
  padding: 1.5em;
  height: 4.5em;
  width: 100%;
  align-items: center;
  box-shadow: 0 0 5px #000000;
  position: fixed;
  top: 0;
  z-index: 1000;
}

.title > a {
  font-size: 1.4em;
  font-weight: bold;
  color: #2c3e50 !important;
  text-decoration: none;
}

.hamburger {
  display: none;
  font-size: 1.8em;
  cursor: pointer;
}

.options {
  list-style: none;
  display: flex;
  justify-content: space-around;
  transition: all 0.3s ease;
}

.options li {
  margin: 0 0.5em;
  font-size: 1.2em;
}

.options li:hover {
  cursor: pointer;
  font-weight: bold;
}

.options a {
  text-decoration: none;
  color: #2c3e50; /* ✅ 強化文字顏色，避免背景色干擾 */
}

/* 🔽 RWD 漢堡選單樣式 */
@media (max-width: 768px) {
  .hamburger {
    display: block;
  }

  .options {
    position: absolute;
    top: 4.5em;
    left: 0;
    width: 100%;
    flex-direction: column;
    background-color: #f3f3f3;
    display: none;
    padding: 1em;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  }

  .options.open {
    display: flex;
  }

  .options li {
    margin: 0.5em 0;
    text-align: center;
  }
}
</style>
