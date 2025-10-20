import React from 'react';

interface BlobAnimationProps {
  // Optional props for customization
  primaryColor?: string;
  backgroundColor?: string;
  size?: string;
}

interface ColorPalette {
  blob1: string;
  blob2: string;
  blob3: string;
  blob4: string;
}

const BlobAnimation: React.FC<BlobAnimationProps> = ({
  primaryColor = "#6ee7b7",
  backgroundColor = '#242424',
  size = 'min(20vw, 20vh)'
}) => {
  // Generate color palette based on primary color
  const generatePalette = (baseColor: string): ColorPalette => {
    // For this example, we're using predefined colors that complement the mint green
    return {
      blob1: baseColor, // Primary color
      blob2: '#34d399', // Darker mint
      blob3: '#a7f3d0', // Lighter mint
      blob4: '#064e3b', // Dark green
    };
  };

  const palette = generatePalette(primaryColor);

  // SVG path animations
  const pathAnimations = {
    first: [
      "M 100 600 q 0 -500, 500 -500 t 500 500 t -500 500 T 100 600 z",
      "M 100 600 q -50 -400, 500 -500 t 450 550 t -500 500 T 100 600 z",
      "M 100 600 q 0 -400, 500 -500 t 400 500 t -500 500 T 100 600 z",
      "M 150 600 q 0 -600, 500 -500 t 500 550 t -500 500 T 150 600 z"
    ],
    second: [
      "M 100 600 q 0 -400, 500 -500 t 400 500 t -500 500 T 100 600 z",
      "M 150 600 q 0 -600, 500 -500 t 500 550 t -500 500 T 150 600 z",
      "M 100 600 q -50 -400, 500 -500 t 450 550 t -500 500 T 100 600 z",
      "M 100 600 q 100 -600, 500 -500 t 400 500 t -500 500 T 100 600 z"
    ]
  };

  return (
    <div  
      style={{ 
        width: '100%', 
        backgroundColor,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      <div 
        className="blobs"
        style={{
          width: size,
          height: size,
          maxHeight: '100%',
          maxWidth: '100%'
        }}
      >
        <svg 
          viewBox="0 0 1200 1200" 
          style={{
            position: 'relative',
            height: '100%',
            zIndex: 2
          }}
        >
          {/* Generate blob groups */}
          {[1, 2, 3, 4].map((blobNum) => (
            <React.Fragment key={blobNum}>
              <g className={`blob blob-${blobNum}`}>
                <path />
              </g>
              <g className={`blob blob-${blobNum} alt`}>
                <path />
              </g>
            </React.Fragment>
          ))}
        </svg>
      </div>

      <style jsx global>{`
        .blob {
          animation: rotate 25s infinite alternate ease-in-out;
          transform-origin: 50% 50%;
          opacity: 0.7;
        }

        .blob path {
          animation: blob-anim-1 5s infinite alternate cubic-bezier(0.45, 0.2, 0.55, 0.8);
          transform-origin: 50% 50%;
          transform: scale(0.8);
          transition: fill 800ms ease;
        }

        .blob.alt {
          animation-direction: alternate-reverse;
          opacity: 0.3;
        }

        .blob-1 path {
          fill: ${palette.blob1};
          filter: blur(1rem);
        }

        .blob-2 {
          animation-duration: 18s;
          animation-direction: alternate-reverse;
        }

        .blob-2 path {
          fill: ${palette.blob2};
          animation-name: blob-anim-2;
          animation-duration: 7s;
          filter: blur(0.75rem);
          transform: scale(0.78);
        }

        .blob-2.alt {
          animation-direction: alternate;
        }

        .blob-3 {
          animation-duration: 23s;
        }

        .blob-3 path {
          fill: ${palette.blob3};
          animation-name: blob-anim-3;
          animation-duration: 6s;
          filter: blur(0.5rem);
          transform: scale(0.76);
        }

        .blob-4 {
          animation-duration: 31s;
          animation-direction: alternate-reverse;
          opacity: 0.9;
        }

        .blob-4 path {
          fill: ${palette.blob4};
          animation-name: blob-anim-4;
          animation-duration: 10s;
          filter: blur(10rem);
          transform: scale(0.5);
        }

        .blob-4.alt {
          animation-direction: alternate;
          opacity: 0.8;
        }

        @keyframes blob-anim-1 {
          0% { d: path("${pathAnimations.first[0]}"); }
          30% { d: path("${pathAnimations.first[1]}"); }
          70% { d: path("${pathAnimations.first[2]}"); }
          100% { d: path("${pathAnimations.first[3]}"); }
        }

        @keyframes blob-anim-2 {
          0% { d: path("${pathAnimations.second[0]}"); }
          40% { d: path("${pathAnimations.second[1]}"); }
          80% { d: path("${pathAnimations.second[2]}"); }
          100% { d: path("${pathAnimations.second[3]}"); }
        }

        @keyframes blob-anim-3 {
          0% { d: path("${pathAnimations.second[2]}"); }
          35% { d: path("${pathAnimations.first[3]}"); }
          75% { d: path("${pathAnimations.second[3]}"); }
          100% { d: path("${pathAnimations.first[2]}"); }
        }

        @keyframes blob-anim-4 {
          0% { d: path("${pathAnimations.first[3]}"); }
          30% { d: path("${pathAnimations.second[3]}"); }
          70% { d: path("${pathAnimations.second[2]}"); }
          100% { d: path("${pathAnimations.first[3]}"); }
        }

        @keyframes rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default BlobAnimation;