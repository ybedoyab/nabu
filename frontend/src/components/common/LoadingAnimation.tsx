import { motion } from 'motion/react';

interface LoadingAnimationProps {
  message?: string;
  isFullScreen?: boolean;
}

const LoadingAnimation: React.FC<LoadingAnimationProps> = ({ 
  message = "AI is working...", 
  isFullScreen = false 
}) => {
  const containerClass = isFullScreen 
    ? "fixed inset-0 z-50 flex items-center justify-center bg-base-100/80 backdrop-blur-sm"
    : "min-h-screen flex items-center justify-center bg-gradient-to-br from-base-100 via-base-200 to-base-100";

  return (
    <motion.div
      className={containerClass}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="flex flex-col items-center justify-center p-8">
        {/* Orbital System */}
        <div className="relative w-40 h-40 mb-6">
          {/* Center Core (represents Earth/research hub) */}
          <motion.div
            className="absolute top-1/2 left-1/2 w-8 h-8 -mt-4 -ml-4 bg-primary rounded-full shadow-lg"
            animate={{
              scale: [1, 1.1, 1],
              opacity: [0.8, 1, 0.8],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <div className="absolute inset-0 bg-primary/30 rounded-full animate-ping" />
          </motion.div>

          {/* Orbit Ring 1 */}
          <motion.div
            className="absolute inset-0 border-2 border-primary/20 rounded-full"
            animate={{ rotate: 360 }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "linear",
            }}
          >
            <motion.div
              className="absolute top-0 left-1/2 w-4 h-4 -ml-2 -mt-2 bg-secondary rounded-full shadow-md"
              animate={{
                scale: [1, 1.2, 1],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          </motion.div>

          {/* Orbit Ring 2 */}
          <motion.div
            className="absolute inset-4 border-2 border-accent/20 rounded-full"
            animate={{ rotate: -360 }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: "linear",
            }}
          >
            <motion.div
              className="absolute bottom-0 left-1/2 w-3 h-3 -ml-1.5 -mb-1.5 bg-accent rounded-full shadow-md"
              animate={{
                scale: [1, 1.3, 1],
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.3,
              }}
            />
          </motion.div>

          {/* Orbit Ring 3 */}
          <motion.div
            className="absolute inset-8 border-2 border-info/20 rounded-full"
            animate={{ rotate: 360 }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: "linear",
            }}
          >
            <motion.div
              className="absolute top-1/2 right-0 w-3 h-3 -mr-1.5 -mt-1.5 bg-info rounded-full shadow-md"
              animate={{
                scale: [1, 1.2, 1],
              }}
              transition={{
                duration: 1.8,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.6,
              }}
            />
          </motion.div>
        </div>

        {/* Loading Text */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <h3 className="text-lg font-semibold text-primary mb-2">
            {message}
          </h3>
        </motion.div>

        {/* Progress Dots */}
        <div className="flex gap-2 mt-6">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 bg-primary rounded-full"
              animate={{
                y: [0, -10, 0],
                opacity: [0.3, 1, 0.3],
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: i * 0.2,
              }}
            />
          ))}
        </div>

        {/* Floating Particles */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-primary/30 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, -100, 0],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: 3 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2,
                ease: "easeInOut",
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default LoadingAnimation;
