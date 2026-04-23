import Footer from "../components/layout/Footer";
import HeroSection from "../components/layout/HeroSection";
import Navbar from "../components/layout/Navbar";
import BackgroundImg from "../assets/background-nabu.png";

const Home = () => {
  return (
    <div className="min-h-screen flex flex-col relative">
      <div
        className="fixed inset-0 bg-cover bg-center bg-no-repeat z-0"
        style={{ backgroundImage: `url(${BackgroundImg})` }}
      />
      <div className="fixed inset-0 bg-black/60 z-0" />
      <div className="fixed inset-0 bg-gradient-to-b from-base-100 via-base-100/80 via-40% to-transparent z-0" />

      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <HeroSection />
        <Footer />
      </div>
    </div>
  );
};

export default Home;
